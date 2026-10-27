"""
Template helpers for Kenyan localisation.

Registered as a template *builtin* in settings, so every template (including
print/PDF templates rendered without a request) can use these without
``{% load %}``:

    {% currency %}                -> KSh
    {{ invoice.net_amount|ksh }}  -> KSh 12,500.00
    {% hospital "address" %}      -> value of settings.HOSPITAL_ADDRESS
    {{ user.phone|ke_phone }}     -> +254 712 345 678
"""
from decimal import Decimal, InvalidOperation

from django import template
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma

from core.kenya import format_phone

register = template.Library()

_HOSPITAL_KEYS = {
    'name': 'HOSPITAL_NAME',
    'short_name': 'HOSPITAL_SHORT_NAME',
    'tagline': 'HOSPITAL_TAGLINE',
    'phone': 'HOSPITAL_PHONE',
    'email': 'HOSPITAL_EMAIL',
    'address': 'HOSPITAL_ADDRESS',
    'website': 'HOSPITAL_WEBSITE',
    'kra_pin': 'HOSPITAL_KRA_PIN',
    'mfl_code': 'HOSPITAL_MFL_CODE',
    'paybill': 'MPESA_SHORTCODE',
}


@register.simple_tag
def currency():
    return getattr(settings, 'CURRENCY_SYMBOL', 'KSh')


@register.simple_tag
def hospital(key):
    setting = _HOSPITAL_KEYS.get(key)
    return getattr(settings, setting, '') if setting else ''


@register.filter
def ksh(value, decimals=2):
    """Format a number as Kenyan shillings with thousands separators."""
    if value in (None, ''):
        value = 0
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value
    decimals = int(decimals)
    formatted = intcomma(f'{amount:.{decimals}f}')
    return f'{currency()} {formatted}'


@register.filter
def ke_phone(value):
    return format_phone(value) if value else value
