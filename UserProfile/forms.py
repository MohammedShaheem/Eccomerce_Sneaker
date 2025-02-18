from django import forms
from UserProfile.models import UserTable,Address
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

class UserRegForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'username',
            'class': 'w-full border rounded px-4 py-2',
            'placeholder': 'Username'
        }),
        required=True,
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_.-]+$',
                message='Username can only contain letters, numbers, and ./-/_ characters.',
                code='invalid_username'
            )
        ]
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'id': 'email',
            'class': 'w-full border rounded px-4 py-2',
            'placeholder': 'your@gmail.com'
        }),
        required=True
    )
    Phone_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'Phone_number',
            'class': 'w-full border rounded px-4 py-2',
            'placeholder': '1234567890'
        }),
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message='Enter a valid 10-digit phone number starting with 6, 7, 8, or 9.',
                code='invalid_phone_number'
            )
        ]
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'password',
            'class': 'w-full border rounded px-4 py-2',
            'placeholder': '••••••••'
        }),
        required=True,
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$',
                message='Password must be at least 8 characters long and include a letter and a number.',
                code='invalid_password'
            )
        ]
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'confirm_password',
            'class': 'w-full border rounded px-4 py-2',
            'placeholder': '••••••••'
        }),
        required=True
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserTable.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data

    class Meta:
        model = UserTable
        fields = ['username', 'email', 'Phone_number', 'password', 'confirm_password']

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ['user','created_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Full Name'
            }),
            'house_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'House/Apartment Name'
            }),
            'street': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Street Address'
            }),
            'landmark': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Landmark (Optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'State'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Pincode',
                'maxlength': '6',
                'pattern': '[0-9]{6}'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'Phone Number',
                'maxlength': '10',
                'pattern': '[0-9]{10}'
            }),
            'address_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500'
            })
        }
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError("Phone number must be 10 digits")
        return pincode
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Phone number must be 10 digits")
        return phone

    def save(self, commit=True):
        instance = super().save(commit=False)
    
        if commit:
        
            instance.save()
    
        return instance