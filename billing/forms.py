from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from core.kenya import KenyanPhoneFormMixin, validate_mpesa_code
from .models import Invoice, InvoiceItem, Payment


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['patient', 'appointment', 'discount', 'tax', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('patient', css_class='col-md-6'),
                Column('appointment', css_class='col-md-6'),
            ),
            Row(
                Column('discount', css_class='col-md-6'),
                Column('tax', css_class='col-md-6'),
            ),
            'notes',
            Div(
                Submit('submit', 'Save Invoice', css_class='btn btn-primary'),
                css_class='mt-3'
            )
        )


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('description', css_class='col-md-5'),
                Column('quantity', css_class='col-md-3'),
                Column('unit_price', css_class='col-md-4'),
            ),
            Div(
                Submit('submit', 'Add Item', css_class='btn btn-success'),
                css_class='mt-3'
            )
        )


class PaymentForm(KenyanPhoneFormMixin, forms.ModelForm):
    phone_fields = ('payer_phone',)

    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'transaction_id', 'payer_phone', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('amount', css_class='col-md-6'),
                Column('payment_method', css_class='col-md-6'),
            ),
            Row(
                Column('transaction_id', css_class='col-md-6'),
                Column('payer_phone', css_class='col-md-6'),
            ),
            'notes',
            Div(
                Submit('submit', 'Record Payment', css_class='btn btn-success'),
                css_class='mt-3'
            )
        )
        self._add_phone_placeholders()

    def clean_transaction_id(self):
        return (self.cleaned_data.get('transaction_id') or '').strip().upper()

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        ref = cleaned.get('transaction_id')
        if method == 'M-Pesa':
            if not ref:
                self.add_error('transaction_id', 'Enter the M-Pesa transaction code from the confirmation SMS.')
            else:
                try:
                    validate_mpesa_code(ref)
                except forms.ValidationError as e:
                    self.add_error('transaction_id', e)
                else:
                    if Payment.objects.filter(payment_method='M-Pesa', transaction_id=ref).exists():
                        self.add_error('transaction_id', 'This M-Pesa code has already been recorded against another payment.')
        elif method in ('Airtel Money', 'Bank Transfer', 'Cheque', 'SHA') and not ref:
            self.add_error('transaction_id', 'A reference number is required for this payment method.')
        return cleaned


class InvoiceFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All')] + Invoice.STATUS_CHOICES
    search = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Search invoice...'}))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='col-md-8'),
                Column('status', css_class='col-md-4'),
            ),
            Div(
                Submit('submit', 'Filter', css_class='btn btn-primary btn-sm'),
                css_class='mt-2'
            )
        )
