from django.db import transaction

from core.services import BaseService
from core.services.utils import check_authentication, output_exception, output_result_success, model_representation
from invoice.models import PaymentInvoice, Invoice, DetailPaymentInvoice
from invoice.utils import resolve_payment_details
from invoice.validation.paymentInvoice import PaymentInvoiceModelValidation


class PaymentInvoiceService(BaseService):

    OBJECT_TYPE = PaymentInvoice

    def __init__(self, user, validation_class: PaymentInvoiceModelValidation = PaymentInvoiceModelValidation):
        super().__init__(user, validation_class)
        self.validation_class = validation_class

    @check_authentication
    def update(self, obj_data):
        raise NotImplementedError("Update method is not implemented for PaymentInvoice")

    @check_authentication
    def create(self, obj_data):
        raise NotImplementedError("Create method is not implemented for PaymentInvoice")

    @check_authentication
    def ref_received(self, payment_invoice: PaymentInvoice, payment_ref):
        try:
            with transaction.atomic():
                self.validation_class.validate_ref_received(self.user, payment_invoice, payment_ref)
                payment_invoice.code_ext = payment_ref
                return self.save_instance(payment_invoice)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="ref_received", exception=exc)

    def payment_received(self, payment_invoice: PaymentInvoice, payment_status: DetailPaymentInvoice.DetailPaymentStatus):
        try:
            with transaction.atomic():
                self.validation_class.validate_receive_payment(self.user, payment_invoice)
                self._update_all_dependencies_for_payment(
                    payment_invoice,
                    payment_status,
                    Invoice.Status.PAYED
                )
                dict_repr = model_representation(payment_invoice)
                return output_result_success(dict_representation=dict_repr)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="payment_received", exception=exc)

    def payment_refunded(self, payment_invoice):
        try:
            with transaction.atomic():
                self._update_all_dependencies_for_payment(
                    payment_invoice,
                    DetailPaymentInvoice.DetailPaymentStatus.REFUNDED,
                    Invoice.Status.SUSPENDED
                )
                dict_repr = model_representation(payment_invoice)
                return output_result_success(dict_representation=dict_repr)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="payment_refunded", exception=exc)

    def payment_cancelled(self, payment_invoice):
        try:
            with transaction.atomic():
                self._update_all_dependencies_for_payment(
                    payment_invoice,
                    DetailPaymentInvoice.DetailPaymentStatus.CANCELLED,
                    Invoice.Status.SUSPENDED
                )
                dict_repr = model_representation(payment_invoice)
                return output_result_success(dict_representation=dict_repr)
        except Exception as exc:
            return output_exception(model_name="PaymentInvoice", method="payment_cancelled", exception=exc)

    def _update_all_dependencies_for_payment(self, payment_invoice, payment_status, invoice_status):
        invoices, bills = resolve_payment_details(payment_invoice)
        payment_details = payment_invoice.invoice_payments.all()
        for pd in payment_details:
            if pd.status != payment_status:
                self._update_payment_status(pd, payment_status)
                pd.save(username=self.user.username)
        for invoice in invoices:
            if invoice.status != invoice_status:
                self._update_invoice_status(invoice, invoice_status)
                invoice.save(username=self.user.username)
        for bill in bills:
            if bill.status != invoice_status:
                self._update_invoice_status(bill, invoice_status)
                bill.save(username=self.user.username)

    def _update_payment_status(self, detail_invoice_payment: DetailPaymentInvoice, status: DetailPaymentInvoice.DetailPaymentStatus):
        detail_invoice_payment.status = status

    def _update_invoice_status(self, invoice_payment, status):
        invoice_payment.status = status