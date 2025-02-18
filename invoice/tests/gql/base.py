from graphene import Schema
from graphene.test import Client
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product

from core.forms import User
from django.test import TestCase

from contract.tests.helpers import create_test_contract
from policyholder.tests.helpers import create_test_policy_holder
from insuree.test_helpers import create_test_insuree

from invoice import schema as invoice_schema
from invoice.tests.helpers import create_test_invoice, \
    create_test_invoice_line_item
from invoice.tests.helpers.invoice_payment_helpers import create_test_invoice_payment


class InvoiceGQLTestCase(TestCase):
    class BaseTestContext:
        def __init__(self, user):
            self.user = user

    @classmethod
    def setUpClass(cls):
        super(InvoiceGQLTestCase, cls).setUpClass()
        cls._graphene_setup()

        cls.maxDiff = None
        if not User.objects.filter(username='admin_invoice').first():
            User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')

        cls.user = User.objects.filter(username='admin_invoice').first()

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
        cls.invoice_payment = create_test_invoice_payment(invoice=cls.invoice, user=cls.user)

    @classmethod
    def _graphene_setup(cls):
        cls.schema = Schema(
            query=invoice_schema.Query,
            mutation=invoice_schema.Mutation
        )
        cls.graph_client = Client(cls.schema)
