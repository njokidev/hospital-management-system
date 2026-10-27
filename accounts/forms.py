from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from core.kenya import KenyanPhoneFormMixin, validate_national_id
from .models import User, Role


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='mb-3'),
            Field('password', css_class='mb-3'),
            Div(
                Submit('submit', 'Login', css_class='btn btn-primary btn-block'),
                css_class='d-grid gap-2'
            )
        )


class PatientRegistrationForm(KenyanPhoneFormMixin, UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        help_text='Used for appointment reminders and M-Pesa payments.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '07XX XXX XXX'
        })
    )
    national_id = forms.CharField(
        label='National ID number',
        max_length=12,
        required=False,
        validators=[validate_national_id],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID (optional)'})
    )
    sha_number = forms.CharField(
        label='SHA member number',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SHA number (optional)'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        }),
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        }),
        help_text='Enter the same password for verification.'
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender')] + User.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone',
                  'password1', 'password2', 'date_of_birth', 'gender']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6 mb-3'),
                Column('last_name', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('email', css_class='col-md-6 mb-3'),
                Column('phone', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('national_id', css_class='col-md-6 mb-3'),
                Column('sha_number', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('username', css_class='col-md-6 mb-3'),
                Column('gender', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('password1', css_class='col-md-6 mb-3'),
                Column('password2', css_class='col-md-6 mb-3'),
            ),
            Field('date_of_birth', css_class='mb-3'),
            Div(
                Submit('submit', 'Register as Patient', css_class='btn btn-success btn-block'),
                css_class='d-grid gap-2 mt-3'
            )
        )

    def clean_national_id(self):
        nid = (self.cleaned_data.get('national_id') or '').strip()
        if nid:
            from patients.models import Patient
            if Patient.objects.filter(id_type='national_id', id_number=nid).exists():
                raise forms.ValidationError('A patient with this National ID is already registered. Please sign in or visit reception.')
        return nid

    def clean_sha_number(self):
        return (self.cleaned_data.get('sha_number') or '').strip().upper()


class UserUpdateForm(KenyanPhoneFormMixin, forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '07XX XXX XXX'
        })
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender')] + User.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Address',
            'rows': 3
        })
    )
    profile_picture = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone',
                  'date_of_birth', 'gender', 'address', 'profile_picture', 'roles', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6 mb-3'),
                Column('last_name', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('email', css_class='col-md-6 mb-3'),
                Column('phone', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('username', css_class='col-md-6 mb-3'),
                Column('gender', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('date_of_birth', css_class='col-md-6 mb-3'),
                Column('profile_picture', css_class='col-md-6 mb-3'),
            ),
            Field('address', css_class='mb-3'),
            Field('roles', css_class='mb-3'),
            Div(
                Submit('submit', 'Update Profile', css_class='btn btn-primary btn-block'),
                css_class='d-grid gap-2 mt-3'
            )
        )


class RoleForm(forms.ModelForm):
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Role Name'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Description',
            'rows': 3
        })
    )

    class Meta:
        model = Role
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            Div(
                Submit('submit', 'Save Role', css_class='btn btn-primary btn-block'),
                css_class='d-grid gap-2 mt-3'
            )
        )
