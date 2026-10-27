import json
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role, User
from patients.models import Patient

from . import mpesa
from .forms import PaymentForm
from .models import Invoice, MpesaTransaction, Payment

MPESA_SETTINGS = dict(
    MPESA_CONSUMER_KEY='key', MPESA_CONSUMER_SECRET='secret', MPESA_SHORTCODE='174379',
    MPESA_PASSKEY='passkey', MPESA_CALLBACK_BASE_URL='https://hms.example.co.ke',
    MPESA_CALLBACK_TOKEN='s3cret',
)


def stk_callback(checkout_id, result_code=0, amount=1500, receipt='SJK4H7XY2Q', phone=254712345678):
    cb = {
        'MerchantRequestID': '29115-34620561-1',
        'CheckoutRequestID': checkout_id,
        'ResultCode': result_code,
        'ResultDesc': 'The service request is processed successfully.' if result_code == 0 else 'Request cancelled by user',
    }
    if result_code == 0:
        cb['CallbackMetadata'] = {'Item': [
            {'Name': 'Amount', 'Value': amount},
            {'Name': 'MpesaReceiptNumber', 'Value': receipt},
            {'Name': 'Balance'},
            {'Name': 'TransactionDate', 'Value': 20261027164400},
            {'Name': 'PhoneNumber', 'Value': phone},
        ]}
    return {'Body': {'stkCallback': cb}}


class BillingTestBase(TestCase):
    def setUp(self):
        self.accountant = User.objects.create_user('acc', password='pw')
        self.accountant.roles.add(Role.objects.create(name='Accountant'))
        self.patient_user = User.objects.create_user('pat', password='pw', phone='+254712345678')
        self.patient = Patient.objects.create(user=self.patient_user)
        self.other_user = User.objects.create_user('other', password='pw')
        self.invoice = Invoice.objects.create(patient=self.patient, total_amount=Decimal('1500.00'))


class PaymentFormTests(BillingTestBase):
    def test_mpesa_requires_valid_code(self):
        form = PaymentForm(data={'amount': '100', 'payment_method': 'M-Pesa', 'transaction_id': ''})
        self.assertIn('transaction_id', form.errors)
        form = PaymentForm(data={'amount': '100', 'payment_method': 'M-Pesa', 'transaction_id': 'bad'})
        self.assertIn('transaction_id', form.errors)
        form = PaymentForm(data={'amount': '100', 'payment_method': 'M-Pesa', 'transaction_id': 'sjk4h7xy2q',
                                 'payer_phone': '0712345678'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['transaction_id'], 'SJK4H7XY2Q')
        self.assertEqual(form.cleaned_data['payer_phone'], '+254712345678')

    def test_mpesa_code_cannot_be_reused(self):
        Payment.objects.create(invoice=self.invoice, amount=10, payment_method='M-Pesa', transaction_id='SJK4H7XY2Q')
        form = PaymentForm(data={'amount': '100', 'payment_method': 'M-Pesa', 'transaction_id': 'SJK4H7XY2Q'})
        self.assertIn('transaction_id', form.errors)

    def test_cash_needs_no_reference(self):
        form = PaymentForm(data={'amount': '100', 'payment_method': 'Cash'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_manual_payment_updates_invoice_status(self):
        self.client.force_login(self.accountant)
        self.client.post(reverse('billing:payment_create', args=[self.invoice.pk]),
                         {'amount': '500', 'payment_method': 'Cash'})
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'Partial')
        self.client.post(reverse('billing:payment_create', args=[self.invoice.pk]),
                         {'amount': '1000', 'payment_method': 'M-Pesa', 'transaction_id': 'SAB1234567'})
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'Paid')
        self.assertEqual(self.invoice.due_amount, 0)


class MpesaClientTests(TestCase):
    @override_settings(**MPESA_SETTINGS)
    def test_stk_push_payload(self):
        token_resp = mock.Mock(status_code=200, json=lambda: {'access_token': 'tok', 'expires_in': '3599'})
        token_resp.raise_for_status = lambda: None
        push_resp = mock.Mock(status_code=200, json=lambda: {
            'MerchantRequestID': 'm1', 'CheckoutRequestID': 'ws_CO_1', 'ResponseCode': '0'})
        with mock.patch('billing.mpesa.requests.get', return_value=token_resp), \
                mock.patch('billing.mpesa.requests.post', return_value=push_resp) as post:
            data = mpesa.stk_push('254712345678', Decimal('1500'), 'INV-000123456789', 'Hospital bill')
        self.assertEqual(data['CheckoutRequestID'], 'ws_CO_1')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['Amount'], 1500)
        self.assertEqual(payload['PartyA'], '254712345678')
        self.assertEqual(payload['AccountReference'], 'INV-00012345')  # trimmed to 12 chars
        self.assertEqual(payload['CallBackURL'], 'https://hms.example.co.ke/billing/mpesa/callback/s3cret/')
        self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer tok')

    def test_not_configured(self):
        with self.assertRaises(mpesa.MpesaError):
            mpesa.stk_push('254712345678', 10, 'INV', 'x')


@override_settings(**MPESA_SETTINGS)
class MpesaFlowTests(BillingTestBase):
    def push(self, user, **data):
        self.client.force_login(user)
        payload = {'phone': '0712345678', 'amount': '1500'}
        payload.update(data)
        with mock.patch('billing.mpesa.stk_push', return_value={
                'MerchantRequestID': 'm1', 'CheckoutRequestID': 'ws_CO_TEST', 'ResponseCode': '0'}) as push:
            resp = self.client.post(reverse('billing:mpesa_stk_push', args=[self.invoice.pk]), payload)
        return resp, push

    def callback(self, body, token='s3cret'):
        return self.client.post(reverse('billing:mpesa_callback', args=[token]),
                                data=json.dumps(body), content_type='application/json')

    def test_patient_can_pay_own_invoice(self):
        resp, push = self.push(self.patient_user)
        self.assertEqual(resp.status_code, 302)
        push.assert_called_once()
        self.assertEqual(push.call_args.args[0], '254712345678')
        self.assertTrue(MpesaTransaction.objects.filter(checkout_request_id='ws_CO_TEST', status='Pending').exists())

    def test_other_users_cannot_push(self):
        _, push = self.push(self.other_user)
        push.assert_not_called()

    def test_amount_cannot_exceed_balance(self):
        _, push = self.push(self.accountant, amount='5000')
        push.assert_not_called()

    def test_successful_callback_records_payment(self):
        self.push(self.accountant)
        self.client.logout()
        resp = self.callback(stk_callback('ws_CO_TEST'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['ResultCode'], 0)
        txn = MpesaTransaction.objects.get()
        self.assertEqual(txn.status, 'Success')
        self.assertEqual(txn.mpesa_receipt_number, 'SJK4H7XY2Q')
        self.assertEqual(txn.payment.payment_method, 'M-Pesa')
        self.assertEqual(txn.payment.payer_phone, '+254712345678')
        self.assertTrue(hasattr(txn.payment, 'receipt'))
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'Paid')

        # Safaricom may deliver the same callback twice – must not double-post
        self.callback(stk_callback('ws_CO_TEST'))
        self.assertEqual(Payment.objects.count(), 1)

    def test_cancelled_callback(self):
        self.push(self.accountant)
        self.callback(stk_callback('ws_CO_TEST', result_code=1032))
        txn = MpesaTransaction.objects.get()
        self.assertEqual(txn.status, 'Cancelled')
        self.assertIsNone(txn.payment)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'Pending')

    def test_bad_token_rejected(self):
        self.push(self.accountant)
        resp = self.callback(stk_callback('ws_CO_TEST'), token='wrong')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(MpesaTransaction.objects.get().status, 'Pending')

    def test_status_endpoint(self):
        self.push(self.patient_user)
        txn = MpesaTransaction.objects.get()
        resp = self.client.get(reverse('billing:mpesa_status', args=[txn.pk]))
        self.assertEqual(resp.json()['status'], 'Pending')
        self.client.force_login(self.other_user)
        resp = self.client.get(reverse('billing:mpesa_status', args=[txn.pk]))
        self.assertEqual(resp.status_code, 403)
