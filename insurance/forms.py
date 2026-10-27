from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from core.kenya import KenyanPhoneFormMixin
from .models import InsuranceProvider, InsurancePlan, PatientInsurance


class InsuranceProviderForm(KenyanPhoneFormMixin, forms.ModelForm):
    class Meta:
        model = InsuranceProvider
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('contact_person', css_class='col-md-6'),
            ),
            Row(
                Column('phone', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            'address',
            'is_active',
            Div(
                Submit('submit', 'Save Provider', css_class='btn btn-primary'),
                css_class='mt-3'
            )
        )


class InsurancePlanForm(forms.ModelForm):
    class Meta:
        model = InsurancePlan
        fields = ['provider', 'name', 'coverage_percentage', 'max_coverage', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('provider', css_class='col-md-6'),
                Column('name', css_class='col-md-6'),
            ),
            Row(
                Column('coverage_percentage', css_class='col-md-6'),
                Column('max_coverage', css_class='col-md-6'),
            ),
            'description',
            'is_active',
            Div(
                Submit('submit', 'Save Plan', css_class='btn btn-primary'),
                css_class='mt-3'
            )
        )


class PatientInsuranceForm(forms.ModelForm):
    class Meta:
        model = PatientInsurance
        fields = ['patient', 'plan', 'policy_number', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('patient', css_class='col-md-6'),
                Column('plan', css_class='col-md-6'),
            ),
            'policy_number',
            Row(
                Column('start_date', css_class='col-md-6'),
                Column('end_date', css_class='col-md-6'),
            ),
            'is_active',
            Div(
                Submit('submit', 'Save Patient Insurance', css_class='btn btn-primary'),
                css_class='mt-3'
            )
        )
