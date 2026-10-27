from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from core.kenya import KenyanPhoneFormMixin
from .models import Employee, Attendance, LeaveRequest


class EmployeeForm(KenyanPhoneFormMixin, forms.ModelForm):
    phone_fields = ('emergency_phone',)

    class Meta:
        model = Employee
        fields = [
            'user', 'department', 'designation', 'date_of_joining',
            'salary', 'national_id', 'kra_pin', 'nssf_number', 'sha_number',
            'regulatory_body', 'license_number', 'license_expiry',
            'emergency_contact', 'emergency_phone', 'is_active'
        ]
        widgets = {
            'date_of_joining': forms.DateInput(attrs={'type': 'date'}),
            'license_expiry': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {'salary': 'Gross monthly salary (KSh)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('user', css_class='col-md-6'),
                Column('department', css_class='col-md-6'),
            ),
            Row(
                Column('designation', css_class='col-md-6'),
                Column('date_of_joining', css_class='col-md-6'),
            ),
            Row(
                Column('salary', css_class='col-md-6'),
                Column('is_active', css_class='col-md-6'),
            ),
            Row(
                Column('national_id', css_class='col-md-3'),
                Column('kra_pin', css_class='col-md-3'),
                Column('nssf_number', css_class='col-md-3'),
                Column('sha_number', css_class='col-md-3'),
            ),
            Row(
                Column('regulatory_body', css_class='col-md-4'),
                Column('license_number', css_class='col-md-4'),
                Column('license_expiry', css_class='col-md-4'),
            ),
            Row(
                Column('emergency_contact', css_class='col-md-6'),
                Column('emergency_phone', css_class='col-md-6'),
            ),
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )
        self._add_phone_placeholders()
        self.fields['kra_pin'].widget.attrs.setdefault('placeholder', 'A012345678Z')

    def clean_kra_pin(self):
        return (self.cleaned_data.get('kra_pin') or '').strip().upper()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('regulatory_body') and not cleaned.get('license_number'):
            self.add_error('license_number', 'Enter the registration number issued by the selected regulator.')
        return cleaned


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'remarks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('employee', css_class='col-md-6'),
                Column('date', css_class='col-md-6'),
            ),
            Row(
                Column('check_in', css_class='col-md-6'),
                Column('check_out', css_class='col-md-6'),
            ),
            Row(
                Column('status', css_class='col-md-6'),
                Column('remarks', css_class='col-md-6'),
            ),
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('employee', css_class='col-md-6'),
                Column('leave_type', css_class='col-md-6'),
            ),
            Row(
                Column('start_date', css_class='col-md-6'),
                Column('end_date', css_class='col-md-6'),
            ),
            'reason',
            Submit('submit', 'Submit Request', css_class='btn btn-primary'),
        )


class LeaveApprovalForm(forms.Form):
    STATUS_CHOICES = [
        ('Approved', 'Approve'),
        ('Rejected', 'Reject'),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.RadioSelect)
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'status',
            'remarks',
            Submit('submit', 'Submit', css_class='btn btn-primary'),
        )
