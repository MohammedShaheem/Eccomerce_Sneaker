from django import forms
from AdminProfile.models import Product,Category,ProductTable,VarianceTable,Size,Color,Product_Images_Table,Offer,Coupon
from django.forms.widgets import FileInput
from django.core.exceptions import ValidationError
import re
from decimal import Decimal
import os
import datetime
from datetime import date
from django.utils import timezone
from django.db import models

##################################################################################################################################################################################

    
#############################################################################################################################################################################


class ProductForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'name',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Product Name',
            'autocomplete': 'off'
        }),
        max_length=150,
        error_messages={
            'required': 'Product name is required',
            'max_length': 'Product name cannot exceed 150 characters'
        }
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'id': 'description',
            'class': "w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100",
            'placeholder': 'Product Description',
            'rows': 4,
        }),
        max_length=500,
        error_messages={
            'required': 'Product description is required',
            'max_length': 'Description cannot exceed 500 characters'
        }
    )
    
    base_price = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'id': 'price',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Price'
        }),
        max_digits=7,
        decimal_places=2,
        error_messages={
            'required': 'Base price is required',
            'invalid': 'Please enter a valid price',
            'max_digits': 'Price cannot exceed 99999.99',
            'max_decimal_places': 'Price can have up to 2 decimal places'
        },
        min_value=0.01,
        max_value=99999.99
    )
    
    sale_Price = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'id': 'sale_price',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Sale Price'
        }),
        max_digits=7,
        decimal_places=2,
        error_messages={
            'required': 'Sale price is required',
            'invalid': 'Please enter a valid sale price',
            'max_digits': 'Sale price cannot exceed 99999.99',
            'max_decimal_places': 'Sale price can have up to 2 decimal places'
        },
        min_value=0.01,
        max_value=99999.99
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={
            'id': 'category',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
        }),
        error_messages={
            'required': 'Please select a category',
            'invalid_choice': 'Invalid category selected'
        }
    )
    class Meta:
        model = ProductTable
        fields = ['name', 'description', 'base_price', 
                  'sale_Price', 'category']
    
    def clean_base_price(self):
        price = self.cleaned_data.get('base_price')
        if price is not None:
            # Convert to string for regex check
            price_str = str(price)
            
            # Validate price
            if price <= Decimal('0'):
                raise forms.ValidationError("Price must be greater than 0.")
            if price > Decimal('1000000'):
                raise forms.ValidationError('Price cannot exceed 1,000,000')
            
            # Optional regex validation
            if not re.match(r'^\d+(\.\d{1,2})?$', price_str):
                raise forms.ValidationError("Product price must be a valid number")
            
            return price
        return price
        
    def clean_sale_Price(self):  
        sale_price = self.cleaned_data.get('sale_Price')
        base_price = self.cleaned_data.get('base_price')
        
        if sale_price is not None:
            # Convert to string for regex check
            sale_price_str = str(sale_price)
            
            # Validate sale price
            if sale_price <= Decimal('0'):
                raise forms.ValidationError("Sale price must be greater than 0.")
            
            if base_price and sale_price > base_price:
                raise forms.ValidationError("Sale price cannot be higher than the base price.")
            
            if base_price and sale_price < (base_price * Decimal('0.1')):
                raise forms.ValidationError("Sale price cannot be less than 10% of the base price.")
            
            # Optional regex validation
            if not re.match(r'^\d+(\.\d{1,2})?$', sale_price_str):
                raise forms.ValidationError("Product price must be a valid number")
        
        return sale_price
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Remove extra whitespace
            name = ' '.join(name.split())
            
            if len(name) < 2:
                raise forms.ValidationError("Product must be at least 2 characters")
            
            if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
                raise forms.ValidationError("Product name can only contain letters, numbers, spaces, hyphens, and underscores")
        
        return name


###############################################################Variant Form###############################################################################################


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {'multiple': 'multiple'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data and initial:
            return initial
        if isinstance(data, (list, tuple)):
            result = [super().clean(d, initial) for d in data]
        else:
            result = super().clean(data, initial)
        return result


class VariantForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'block w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md focus:ring focus:ring-blue-300 text-white',
            'accept': 'image/*',
            'multiple': True  
        }),
        label = "Variant Images"
    )
    
    size = forms.ModelChoiceField(
        queryset=Size.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-800 border border-gray-600 text-gray-100 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 hover:bg-gray-700 appearance-none',
            'style': 'background-image: url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%23ffffff\' stroke-width=\'2\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' d=\'M19 9l-7 7-7-7\' /%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 1rem center; background-size: 1rem;',
        })
    )
    
    color = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'color',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Enter Color',
        }),
        required=False
    )
    
    
    
    Stock_Quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'block w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md focus:ring focus:ring-blue-300 text-white',
            'min': '0',
        }),
        required=False,
        error_messages={
            'required': 'Stock quantity is required',
            'invalid': 'Please enter a valid number',
            'min_value': 'Quantity cannot be negative'
        },
        min_value=0
    )

    class Meta:
        model = VarianceTable
        fields = ['size','Stock_Quantity']

    def clean_images(self):
        """
        Clean and validate the uploaded images
        """
        def clean_images(self):
            images = self.files.getlist('images') if self.files else []
            for image in images:
                if not image.content_type.startswith('image/'):
                    raise forms.ValidationError(f"File {image.name} is not a valid image")
                if image.size > 5 * 1024 * 1024:  # 5MB limit
                    raise forms.ValidationError(f"Image {image.name} exceeds 5MB size limit")
            return images
        
        def clean_Stock_Quantity(self):
            quantity = self.cleaned_data.get('Stock_Quantity')
            if quantity is not None and quantity < 0:
                raise forms.ValidationError("Stock quantity cannot be negative")
            return quantity
        
        def clean(self):
            cleaned_data = super().clean()
            if 'color' in cleaned_data:
                del cleaned_data['color']
            return cleaned_data


################################################################Category Form##################################################################    
    

class CategoryForm(forms.ModelForm):
    category_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'category_name',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Category Name'
        }),
        max_length=150,
        required=True,
        error_messages={
            'required': 'Category name is required.',
            'max_length': 'Category name cannot exceed 150 characters.'
        }
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'id': 'description',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Category Description',
            'rows': 4,
        }),
        max_length=500,
        required=True,
        error_messages={
            'required': 'Description is required.',
            'max_length': 'Description cannot exceed 500 characters.'
        }
    )
    
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'id': 'image',
            'class': 'sr-only',  # Hidden but accessible
            'accept': 'image/*'
        }),
        required=False,
        error_messages={
            'required': 'Please upload a category image.',
            'invalid_image': 'Please upload a valid image file.'
        }
    )

    class Meta:
        model = Category
        fields = ['category_name', 'description', 'image']

    def clean_category_name(self):
        category_name = self.cleaned_data.get('category_name')
        if category_name:
            # Remove extra whitespace
            category_name = ' '.join(category_name.split())
            
            if len(category_name) < 3:
                raise forms.ValidationError("Category name must be at least 3 characters long")
            
            if not re.match(r"^[a-zA-Z]", category_name):
                raise forms.ValidationError("Category name must start with a letter")
  
            if not re.match(r"^[a-zA-Z0-9\s\-_]+$", category_name):
                raise forms.ValidationError("Category name can only contain letters, numbers, spaces, hyphens, and underscores")
            
            # Check if category name already exists (case-insensitive)
            if Category.objects.filter(category_name__iexact=category_name).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("This category name already exists")
                    
        return category_name

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Debug logging
            print(f"Processing image: {image.name}, Content-Type: {getattr(image, 'content_type', 'N/A')}")
            
            # Handle new uploads
            if hasattr(image, 'content_type'):
                print("New upload detected")
                if image.size > 5 * 1024 * 1024:  # 5 MB limit
                    raise forms.ValidationError("Image size should not exceed 5 MB")
                
                valid_types = ['image/jpeg', 'image/png', 'image/gif']
                if image.content_type not in valid_types:
                    # Additional check using file extension as a fallback
                    ext = os.path.splitext(image.name)[1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                        raise forms.ValidationError("Please upload only JPEG, PNG, or GIF images")
            
            # Handle existing files (e.g., when updating with current image)
            else:
                print("Existing file detected")
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                ext = os.path.splitext(image.name)[1].lower()
                if ext not in valid_extensions:
                    raise forms.ValidationError("Invalid file extension. Only JPEG, PNG, or GIF images are allowed")
            
        return image
##################################################################################################################################################################################################
    
class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            'offer_title',
            'discount_value',
            'discount_type',
            'valid_from',
            'valid_till',
            'offer_description',
            'is_active'
        ]

    def __init__(self, *args, **kwargs):
        offer_type = kwargs.pop('offer_type', None)
        super().__init__(*args, **kwargs)
        
        # Add common styling
        base_class = 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100'
        
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.DateTimeInput)):
                field.widget.attrs.update({'class': base_class})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': base_class,
                    'rows': 3
                })

        # Set minimum date for date fields
        today = date.today().strftime('%Y-%m-%d')
        self.fields['valid_from'].widget.attrs['min'] = today
        self.fields['valid_till'].widget.attrs['min'] = today


        # Add type-specific fields
        if offer_type:
            if offer_type == 'product':
                self.fields['product'] = forms.ModelChoiceField(
                    queryset=ProductTable.objects.filter(Is_deleted=False, Is_active=True),
                    widget=forms.Select(attrs={'class': base_class}),
                    required=True
                )
            else:
                self.fields['category'] = forms.ModelChoiceField(
                    queryset=Category.objects.filter(is_delete=False, status=True),
                    widget=forms.Select(attrs={'class': base_class}),
                    required=True
                )
                
    def clean(self):
        cleaned_data = super().clean()
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        category = cleaned_data.get('category')

        # Validation for category offers with fixed discount
        if category and discount_type == 'fixed' and discount_value is not None:
            # Get the lowest priced product in the category
            lowest_price = ProductTable.objects.filter(
                category=category,
                Is_deleted=False,
                Is_active=True
            ).aggregate(min_price=models.Min('sale_Price'))['min_price']

            if lowest_price is not None:
                min_allowed_discount = lowest_price - 500
                if discount_value >= min_allowed_discount:
                    raise ValidationError(
                        f"The fixed discount amount ({discount_value}₹) must be at least 500₹ less than "
                        f"the lowest priced product in the category ({lowest_price}₹). "
                        f"Maximum allowed discount is {min_allowed_discount}₹."
                    )

        return cleaned_data
##########################################################################################################################################################################################
class CouponCreationForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'coupon_name', 
            'coupon_code', 
            'min_purchase_amount', 
            'discount', 
            'discount_type',
            'valid_from', 
            'valid_till', 
            'max_uses',
            'is_active'
        ]
        widgets = {
            'coupon_name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
                'placeholder': 'Enter coupon name (e.g., Summer Sale 2025)'
            }),
            'coupon_code': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
                'placeholder': 'Enter coupon code (e.g., SUMMER25)'
            }),
            'min_purchase_amount': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-1000',
                'placeholder': 'Minimum order amount required',
                'step': '0.01'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
                'placeholder': 'Discount amount',
                'step': '0.01'
            }),
            'discount_type': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100'
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
                'type': 'datetime-local'
            }),
            'valid_till': forms.DateTimeInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
                'type': 'datetime-local'
            }),
            'max_uses': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
                'placeholder': 'Maximum number of uses'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100'
            })
        }
    
    
    def __init__(self, *args, **kwargs):
        super(CouponCreationForm, self).__init__(*args, **kwargs)
        #makeing all fields required except is_active
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.required = True
                
        #setting defaults for datetime fields if not already set
        if not self.initial.get('valid_from'):
            self.initial['valid_from'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        if not self.initial.get('valid_till'):
            #default end date is 30 days from now
            self.initial['valid_till'] = (timezone.now() + timezone.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_till = cleaned_data.get('valid_till')
        discount = cleaned_data.get('discount')
        discount_type = cleaned_data.get('discount_type')
        
        #validate dates
        if valid_from and valid_till:
            if valid_from >= valid_till:
                raise forms.ValidationError("End date must be after start date.")
        
        #validate discount based on type
        if discount is not None and discount_type:
            if discount_type == 'percent' and discount > 95:
                raise forms.ValidationError({
                    'discount': "Percentage discount cannot exceed 95%."
                })
            elif discount <= 0:
                raise forms.ValidationError({
                    'discount': "Discount must be greater than zero."
                })
        
        #validate min purchase amount
        min_purchase = cleaned_data.get('min_purchase_amount')
        if min_purchase is not None and min_purchase < 0:
            raise forms.ValidationError({
                'min_purchase_amount': "Minimum purchase amount cannot be negative."
            })
            
        #validate coupon code format (optional)
        coupon_code = cleaned_data.get('coupon_code')
        if coupon_code:
            #remove spaces and convert to uppercase
            cleaned_data['coupon_code'] = coupon_code.strip().upper()
            
        return cleaned_data
    
    def clean_coupon_code(self):
        code = self.cleaned_data.get('coupon_code', '').strip().upper()
    
        # Skip validation if this is an update to an existing coupon
        if self.instance.pk and self.instance.coupon_code == code:
            return code
        
        # Only check against non-deleted coupons
        if Coupon.objects.filter(coupon_code=code, is_deleted=False).exists():
            raise forms.ValidationError(
                "This coupon code is already in use. Please choose a different code."
        )   
    
        return code