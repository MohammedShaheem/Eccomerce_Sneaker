from django import forms
from UserProfile.models import UserTable,Address
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re
from AdminProfile.models import Order

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
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Name is required")
        if len(name) < 3 or len(name) > 50:
            raise forms.ValidationError("Name must be between 3 and 50 characters")
        if not re.match(r'^[a-zA-Z\s]*$', name):
            raise forms.ValidationError("Name can only contain letters and spaces")
        return name
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required")
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise forms.ValidationError("Please enter a valid email address")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("Phone number is required")
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Phone number must be 10 digits")
        if not re.match(r'^[6-9]\d{9}$', phone):
            raise forms.ValidationError("Phone number must start with 6, 7, 8, or 9")
        return phone
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode:
            raise forms.ValidationError("Pincode is required")
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError("Pincode must be 6 digits")
        return pincode
    
    def clean_house_name(self):
        house_name = self.cleaned_data.get('house_name')
        if not house_name:
            raise forms.ValidationError("House/Apartment name is required")
        if len(house_name) < 3 or len(house_name) > 100:
            raise forms.ValidationError("House name must be between 3 and 100 characters")
        return house_name
    
    def clean_street(self):
        street = self.cleaned_data.get('street')
        if not street:
            raise forms.ValidationError("Street address is required")
        if len(street) < 5 or len(street) > 100:
            raise forms.ValidationError("Street address must be between 5 and 100 characters")
        return street
    
    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not city:
            raise forms.ValidationError("City is required")
        if not re.match(r'^[a-zA-Z\s]*$', city):
            raise forms.ValidationError("City name can only contain letters and spaces")
        return city
    
    def clean_state(self):
        state = self.cleaned_data.get('state')
        if not state:
            raise forms.ValidationError("State is required")
        if not re.match(r'^[a-zA-Z\s]*$', state):
            raise forms.ValidationError("State name can only contain letters and spaces")
        return state
    
    def clean(self):
        cleaned_data = super().clean()
        # Add any cross-field validation here if needed
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance
    

class CancellationForm(forms.Form):
    REASON_CHOICES = [
        ('changed_mind', 'Changed my mind'),
        ('found_better_price', 'Found a better price elsewhere'),
        ('delayed_delivery', 'Delivery taking too long'),
        ('ordered_mistake', 'Ordered by mistake'),
        ('other', 'Other reason')
    ]
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    additional_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border border-gray-300 px-3 py-2 focus:border-indigo-500 focus:ring-indigo-500',
            'rows': 4,
            'placeholder': 'Please provide any additional details about your cancellation...'
        }),
        required=False
    )
    
    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get('reason')
        additional_details = cleaned_data.get('additional_details')
        
        if reason == 'other' and not additional_details:
            self.add_error('additional_details', 'Please provide details for "Other reason"')
        
        return cleaned_data
    
class ReturnForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        label="Return Reason",
        help_text="Please provide a detailed reason for returning these items."
    )
