from core.forms import User
from invoice.models import BillPayment
from invoice.tests.helpers import create_test_bill
from invoice.tests.helpers.default_test_data import DEFAULT_TEST_BILL_PAYMENT_PAYLOAD


def create_test_bill_payment(bill=None, user=None, **custom_props):
    bill = bill or create_test_bill()
    user = user or __get_or_create_user()

    payload = DEFAULT_TEST_BILL_PAYMENT_PAYLOAD.copy()
    payload.update(**custom_props)
    payment = BillPayment(**payload)
    payment.bill = bill

    payment.save(username=user.username)
    return payment


def __get_or_create_user():
    user = User.objects.filter(username='admin_invoice').first()
    if not user:
        user = User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')
    return user
