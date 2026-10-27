from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from core.kenya import KenyanPhoneFormMixin, validate_id_document
from .models import Patient, MedicalRecord, PatientDocument


class PatientForm(KenyanPhoneFormMixin, forms.ModelForm):
    phone_fields = ('emergency_contact_phone',)

    class Meta:
        model = Patient
        fields = [
            'user', 'id_type', 'id_number', 'sha_number', 'blood_group',
            'county', 'sub_county', 'ward',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone',
            'insurance_provider', 'allergies', 'medical_history',
        ]
        widgets = {
            'allergies': forms.Textarea(attrs={'rows': 3}),
            'medical_history': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_phone_placeholders()
        self.fields['sha_number'].widget.attrs.setdefault('placeholder', 'e.g. SHA-XXXXXXXX')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('user', css_class='col-md-6'),
                Column('blood_group', css_class='col-md-6'),
            ),
            HTML('<h5 class="mt-2">Identification</h5>'),
            Row(
                Column('id_type', css_class='col-md-4'),
                Column('id_number', css_class='col-md-4'),
                Column('sha_number', css_class='col-md-4'),
            ),
            HTML('<h5 class="mt-2">Residence</h5>'),
            Row(
                Column('county', css_class='col-md-4'),
                Column('sub_county', css_class='col-md-4'),
                Column('ward', css_class='col-md-4'),
            ),
            HTML('<h5 class="mt-2">Next of Kin</h5>'),
            Row(
                Column('emergency_contact_name', css_class='col-md-4'),
                Column('emergency_contact_relationship', css_class='col-md-4'),
                Column('emergency_contact_phone', css_class='col-md-4'),
            ),
            'insurance_provider',
            HTML('<hr><h5>Medical Information</h5>'),
            'allergies',
            'medical_history',
            Submit('submit', 'Save Patient', css_class='btn btn-primary'),
        )

    def clean_id_number(self):
        return (self.cleaned_data.get('id_number') or '').strip().upper()

    def clean_sha_number(self):
        return (self.cleaned_data.get('sha_number') or '').strip().upper()

    def clean(self):
        cleaned = super().clean()
        id_type, id_number = cleaned.get('id_type'), cleaned.get('id_number')
        try:
            validate_id_document(id_type, id_number)
        except forms.ValidationError as e:
            for field, errors in e.message_dict.items():
                for err in errors:
                    self.add_error(field, err)
        if id_number and id_type not in (None, '', 'none'):
            clash = Patient.objects.filter(id_type=id_type, id_number=id_number)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                self.add_error('id_number', f'Another patient ({clash.first().patient_id}) is already registered with this document number.')
        sha = cleaned.get('sha_number')
        if sha:
            clash = Patient.objects.filter(sha_number=sha)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                self.add_error('sha_number', f'This SHA number is already linked to {clash.first().patient_id}.')
        return cleaned


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['patient', 'doctor', 'visit_date', 'diagnosis', 'symptoms', 'notes']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'symptoms': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('patient', css_class='col-md-6'),
                Column('doctor', css_class='col-md-6'),
            ),
            'visit_date',
            'diagnosis',
            'symptoms',
            'notes',
            Submit('submit', 'Save Record', css_class='btn btn-primary'),
        )


class PatientDocumentForm(forms.ModelForm):
    class Meta:
        model = PatientDocument
        fields = ['document_type', 'title', 'description', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optional)'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
