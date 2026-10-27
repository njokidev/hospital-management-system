"""
Minimal Safaricom Daraja (M-Pesa) client for Lipa Na M-Pesa Online (STK Push).

Configure through settings / environment variables:

    MPESA_ENVIRONMENT        sandbox | production
    MPESA_CONSUMER_KEY       from the Daraja portal app
    MPESA_CONSUMER_SECRET
    MPESA_SHORTCODE          Paybill or Till (sandbox: 174379)
    MPESA_PASSKEY            Lipa Na M-Pesa Online passkey
    MPESA_TRANSACTION_TYPE   CustomerPayBillOnline | CustomerBuyGoodsOnline
    MPESA_CALLBACK_BASE_URL  public HTTPS URL Safaricom can reach
    MPESA_CALLBACK_TOKEN     secret path segment for the callback URL

Docs: https://developer.safaricom.co.ke/APIs/MpesaExpressSimulate
"""
import base64
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

BASE_URLS = {
    'sandbox': 'https://sandbox.safaricom.co.ke',
    'production': 'https://api.safaricom.co.ke',
}
TIMEOUT = 30


class MpesaError(Exception):
    """Raised when Daraja is misconfigured, unreachable or rejects a request."""


def is_configured():
    return all(getattr(settings, k, '') for k in (
        'MPESA_CONSUMER_KEY', 'MPESA_CONSUMER_SECRET', 'MPESA_SHORTCODE',
        'MPESA_PASSKEY', 'MPESA_CALLBACK_BASE_URL',
    ))


def _base_url():
    return BASE_URLS.get(settings.MPESA_ENVIRONMENT, BASE_URLS['sandbox'])


def get_access_token():
    """OAuth token, cached for slightly less than its 3600 s lifetime."""
    cache_key = f'mpesa_token_{settings.MPESA_ENVIRONMENT}'
    token = cache.get(cache_key)
    if token:
        return token
    try:
        resp = requests.get(
            f'{_base_url()}/oauth/v1/generate?grant_type=client_credentials',
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.exception('M-Pesa OAuth failed')
        raise MpesaError('Could not authenticate with M-Pesa. Check the consumer key/secret.') from exc
    token = data['access_token']
    cache.set(cache_key, token, int(data.get('expires_in', 3599)) - 60)
    return token


def _timestamp():
    # Daraja expects Kenyan local time, YYYYMMDDHHMMSS
    return timezone.localtime().strftime('%Y%m%d%H%M%S')


def _password(timestamp):
    raw = f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'
    return base64.b64encode(raw.encode()).decode()


def callback_url():
    path = reverse('billing:mpesa_callback', kwargs={'token': settings.MPESA_CALLBACK_TOKEN})
    return settings.MPESA_CALLBACK_BASE_URL.rstrip('/') + path


def stk_push(msisdn, amount, account_reference, description):
    """Prompt the customer's phone to authorise a payment.

    ``msisdn`` must be in 2547XXXXXXXX form, ``amount`` a whole number of shillings.
    Returns Daraja's JSON response (MerchantRequestID, CheckoutRequestID, ...).
    """
    if not is_configured():
        raise MpesaError('M-Pesa STK Push is not configured on this server.')
    amount = int(amount)
    if amount < 1:
        raise MpesaError('Amount must be at least KSh 1.')
    ts = _timestamp()
    party_b = settings.MPESA_SHORTCODE
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': _password(ts),
        'Timestamp': ts,
        'TransactionType': settings.MPESA_TRANSACTION_TYPE,
        'Amount': amount,
        'PartyA': msisdn,
        'PartyB': party_b,
        'PhoneNumber': msisdn,
        'CallBackURL': callback_url(),
        'AccountReference': account_reference[:12],   # Daraja limit
        'TransactionDesc': description[:13],          # Daraja limit
    }
    try:
        resp = requests.post(
            f'{_base_url()}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers={'Authorization': f'Bearer {get_access_token()}'},
            timeout=TIMEOUT,
        )
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.exception('M-Pesa STK push request failed')
        raise MpesaError('M-Pesa is not responding right now. Please try again.') from exc
    if resp.status_code != 200 or str(data.get('ResponseCode')) != '0':
        msg = data.get('errorMessage') or data.get('ResponseDescription') or 'Request rejected by M-Pesa.'
        logger.warning('STK push rejected: %s', data)
        raise MpesaError(msg)
    return data


def parse_callback(body):
    """Flatten Daraja's stkCallback payload into a simple dict."""
    cb = body['Body']['stkCallback']
    result = {
        'merchant_request_id': cb.get('MerchantRequestID', ''),
        'checkout_request_id': cb['CheckoutRequestID'],
        'result_code': int(cb.get('ResultCode', -1)),
        'result_desc': cb.get('ResultDesc', ''),
        'amount': None,
        'receipt_number': '',
        'phone': '',
        'transaction_date': None,
    }
    for item in cb.get('CallbackMetadata', {}).get('Item', []):
        name, value = item.get('Name'), item.get('Value')
        if name == 'Amount':
            result['amount'] = value
        elif name == 'MpesaReceiptNumber':
            result['receipt_number'] = str(value)
        elif name == 'PhoneNumber':
            result['phone'] = str(value)
        elif name == 'TransactionDate' and value:
            try:
                naive = datetime.strptime(str(value), '%Y%m%d%H%M%S')
                result['transaction_date'] = timezone.make_aware(naive)
            except ValueError:
                pass
    return result
