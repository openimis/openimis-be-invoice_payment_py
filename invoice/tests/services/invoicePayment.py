import copy
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from policy.test_helpers import create_test_policy
from policyholder.models import PolicyHolder
from product.test_helpers import create_test_product

from contract.models import Contract
from core.forms import User
from django.test import TestCase

from invoice.models import Invoice, InvoiceLineItem, InvoicePayment
from contract.tests.helpers import create_test_contract
from policyholder.tests.helpers import create_test_policy_holder
from insuree.test_helpers import create_test_insuree
from datetime import date

from invoice.services.invoiceLineItem import InvoiceLineItemService
from invoice.services.invoicePayments import InvoicePaymentsService
from invoice.tests.helpers import DEFAULT_TEST_INVOICE_PAYLOAD, create_test_invoice, \
    create_test_invoice_line_item
from invoice.validation.invoicePayment import InvoicePaymentModelValidation
from invoice.validation.paymentStatusValidation import InvoicePaymentRefundStatusValidator, \
    InvoicePaymentReceiveStatusValidator, InvoicePaymentCancelStatusValidator


class ServiceTestInvoicePayments(TestCase):
    BASE_TEST_INVOICE_PAYMENT_PAYLOAD = {
        'label': 'label_pay',
        'code_rcp': 'pay_sys_ref',
        'code_receipt': 'receipt number',
        'invoice': None,
        'amount_payed': 91.5,
        'fees': 12.0,
        'amount_received': 22.0,
        'date_payment': date(2021, 10, 10),
    }

    BASE_EXPECTED_SUCCESS_RESPONSE = {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": {
            'status': 1,
            'label': 'label_pay',
            'code_rcp': 'pay_sys_ref',
            'code_receipt': 'receipt number',
            'amount_payed': 91.5,
            'fees': 12.0,
            'amount_received': 22.00,
            'date_payment': str(date(2021, 10, 10))
        },
    }

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        if not User.objects.filter(username='admin_invoice').exists():
            User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')

        cls.user = User.objects.filter(username='admin_invoice').first()
        cls.invoice_payment_service = InvoicePaymentsService(cls.user)

        cls.policy_holder = create_test_policy_holder()
        cls.contract = create_test_contract(cls.policy_holder)
        cls.insuree = create_test_insuree(with_family=True)
        cls.product = create_test_product("TestC0d3", custom_props={"insurance_period": 12})
        cls.policy = create_test_policy(
            product=cls.product,
            insuree=cls.insuree
        )

        cls.invoice = create_test_invoice(cls.contract, cls.insuree)
        cls.invoice_line_item = \
            create_test_invoice_line_item(invoice=cls.invoice, line_item=cls.policy, user=cls.user)

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        InvoiceLineItem.objects.filter(code=cls.invoice_line_item.code).delete()
        Invoice.objects.filter(code=cls.invoice.code).delete()
        Contract.objects.filter(id=cls.contract.id).delete()
        PolicyHolder.objects.filter(id=cls.policy_holder.id).delete()

        cls.insuree.insuree_policies.first().delete()
        cls.policy.delete()
        cls.insuree.delete()
        cls.product.delete()

        super().tearDownClass()

    def test_ref_received(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD.copy()
            payload['status'] = InvoicePayment.InvoicePaymentStatus.ACCEPTED

            payment = self._create_payment(payload)
            payment.save(username=self.user.username)

            out = self.invoice_payment_service.ref_received(payment, 'code_ext1')
            expected = self.BASE_EXPECTED_SUCCESS_RESPONSE.copy()
            expected['data']['code_ext'] = 'code_ext1'
            self._assert_output_valid(out, payment, expected)
            InvoicePayment.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_received(self):
        with transaction.atomic():
            payment = self._create_payment(self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD)
            out = self.invoice_payment_service.payment_received(payment, InvoicePayment.InvoicePaymentStatus.ACCEPTED)
            self._assert_output_valid(out, payment, self.BASE_EXPECTED_SUCCESS_RESPONSE.copy())
            InvoicePayment.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_received_invalid_amount(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD.copy()
            payload['amount_payed'] = 2.0
            payment = self._create_payment(payload)
            out = self.invoice_payment_service.payment_received(payment, InvoicePayment.InvoicePaymentStatus.ACCEPTED)
            detail = [str(InvoicePaymentModelValidation.AMOUNT_PAYED_NOT_MATCHING_ITEMS \
                     % {'invoice': self.invoice, 'expected': 91.5, 'payed': 2.0})]
            message = 'Failed to payment_received InvoicePayment'
            self._assert_output_invalid(out, message, detail)
            InvoicePayment.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_received_invalid_invoice_status(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD.copy()
            payment = self._create_payment(payload)
            payment.invoice.status = Invoice.InvoiceStatus.CANCELLED
            out = self.invoice_payment_service.payment_received(payment, InvoicePayment.InvoicePaymentStatus.ACCEPTED)
            detail = [str(InvoicePaymentReceiveStatusValidator.error_message_invalid_invoice \
                     % {'invoice': self.invoice, 'allowed_invoice': 'draft, validated', 'invoice_status': self.invoice.status.label})]
            message = 'Failed to payment_received InvoicePayment'
            self._assert_output_invalid(out, message, detail)

            payment.invoice.status = Invoice.InvoiceStatus.VALIDATED
            InvoicePayment.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_received_invalid_payment_status(self):
        with transaction.atomic():
            payload = self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD.copy()
            payload['status'] = InvoicePayment.InvoicePaymentStatus.REFUNDED
            payment = self._create_payment(payload)
            out = self.invoice_payment_service.payment_received(payment, InvoicePayment.InvoicePaymentStatus.REFUNDED)
            detail = [str(InvoicePaymentReceiveStatusValidator.error_message_invalid_payment
                          % {'payment_status': InvoicePayment.InvoicePaymentStatus.REFUNDED.label,
                             'allowed_payment': 'accepted, rejected'})]
            message = 'Failed to payment_received InvoicePayment'
            self._assert_output_invalid(out, message, detail)
            InvoicePayment.objects.filter(code_ext=payment.code_ext).delete()

    def test_payment_refunded(self):
        with transaction.atomic():
            payment = self._create_payment(self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD)
            payment.invoice.status = Invoice.InvoiceStatus.PAYED
            payment.status = InvoicePayment.InvoicePaymentStatus.ACCEPTED

            out = self.invoice_payment_service.payment_refunded(payment)
            expected = copy.deepcopy(self.BASE_EXPECTED_SUCCESS_RESPONSE)
            expected['data']['status'] = 2
            self._assert_output_valid(out, payment, expected)
            self.assertEqual(payment.invoice.status, Invoice.InvoiceStatus.SUSPENDED)
            InvoicePayment.objects.filter(code_ext=payment.code_ext).delete()
            self.invoice.status = Invoice.InvoiceStatus.VALIDATED

    def test_payment_refunded_invalid_invoice_status(self):
        with transaction.atomic():
            payment = self._create_payment(self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD)
            payment.invoice.status = Invoice.InvoiceStatus.CANCELLED
            payment.status = InvoicePayment.InvoicePaymentStatus.ACCEPTED

            out = self.invoice_payment_service.payment_refunded(payment)
            detail = [str(InvoicePaymentRefundStatusValidator.error_message_invalid_invoice
                          % {'invoice': self.invoice,
                             'invoice_status': self.invoice.status.label,
                             'allowed_invoice': Invoice.InvoiceStatus.PAYED.label})]
            message = 'Failed to payment_refunded InvoicePayment'
            self._assert_output_invalid(out, message, detail)
            self.invoice.status = Invoice.InvoiceStatus.VALIDATED

    def test_payment_refunded_invalid_payment_status(self):
        with transaction.atomic():
            payment = self._create_payment(self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD)
            payment.invoice.status = Invoice.InvoiceStatus.PAYED
            payment.status = InvoicePayment.InvoicePaymentStatus.REJECTED

            out = self.invoice_payment_service.payment_refunded(payment)
            detail = [str(InvoicePaymentRefundStatusValidator.error_message_invalid_payment
                          % {'payment_status': payment.status.label, 'payment': payment})]
            message = 'Failed to payment_refunded InvoicePayment'
            self._assert_output_invalid(out, message, detail)
            self.invoice.status = Invoice.InvoiceStatus.VALIDATED

    def test_payment_cancel_invalid_invoice_status(self):
        with transaction.atomic():
            payment = self._create_payment(self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD)
            payment.invoice.status = Invoice.InvoiceStatus.CANCELLED
            payment.status = InvoicePayment.InvoicePaymentStatus.ACCEPTED

            out = self.invoice_payment_service.payment_cancelled(payment)
            detail = [str(InvoicePaymentCancelStatusValidator.error_message_invalid_invoice
                          % {'invoice': self.invoice,
                             'invoice_status': self.invoice.status.label,
                             'allowed_invoice': Invoice.InvoiceStatus.PAYED.label})]
            message = 'Failed to payment_refunded InvoicePayment'
            self._assert_output_invalid(out, message, detail)
            self.invoice.status = Invoice.InvoiceStatus.VALIDATED

    def test_payment_cancel_invalid_payment_status(self):
        with transaction.atomic():
            payment = self._create_payment(self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD)
            payment.invoice.status = Invoice.InvoiceStatus.PAYED
            payment.status = InvoicePayment.InvoicePaymentStatus.REJECTED

            out = self.invoice_payment_service.payment_cancelled(payment)
            detail = [str(InvoicePaymentCancelStatusValidator.error_message_invalid_payment
                          % {'payment_status': payment.status.label, 'payment': payment})]
            message = 'Failed to payment_refunded InvoicePayment'
            self._assert_output_invalid(out, message, detail)
            self.invoice.status = Invoice.InvoiceStatus.VALIDATED

    def test_payment_cancelled(self):
        with transaction.atomic():
            payment = self._create_payment(self.BASE_TEST_INVOICE_PAYMENT_PAYLOAD)
            payment.invoice.status = Invoice.InvoiceStatus.PAYED
            payment.status = InvoicePayment.InvoicePaymentStatus.ACCEPTED

            out = self.invoice_payment_service.payment_cancelled(payment)
            expected = copy.deepcopy(self.BASE_EXPECTED_SUCCESS_RESPONSE)
            self._assert_output_valid(out, payment, expected)
            InvoicePayment.objects.filter(code_ext=payment.code_ext).delete()
            self.assertEqual(payment.invoice.status, Invoice.InvoiceStatus.SUSPENDED)
            self.invoice.status = Invoice.InvoiceStatus.VALIDATED

    def _create_payment(self, args):
        payment = InvoicePayment(**args)
        payment.invoice = self.invoice
        return payment

    def _assert_output_valid(self, out, payment, expected):
        expected['data']['invoice'] = str(self.invoice.uuid)
        expected['data']['id'] = str(payment.id)
        out['data'] = {k: v for k, v in out['data'].items() if k in expected['data'].keys()}
        self.assertDictEqual(out, expected)

    def _assert_output_invalid(self, out, message, detail):
        expected = {
            'success': False,
            'message': message,
            'detail': str(detail).replace('\'', '').replace('\"', ''),
            'data': ''
        }
        out['detail'] = out['detail'].replace('\'', '').replace('\"', '')
        self.assertDictEqual(out, expected)