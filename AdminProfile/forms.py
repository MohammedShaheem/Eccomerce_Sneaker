from django import forms
from AdminProfile.models import Product,Category,ProductTable,VarianceTable,Size,Color,Product_Images_Table
from django.forms.widgets import FileInput
from django.core.exceptions import ValidationError
import re
from decimal import Decimal

##################################################################################################################################################################################

class MultipleFileInput(FileInput):
    def __init__(self, attrs=None):
        default_attrs = {'multiple':'multiple'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
        
        
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget",MultipleFileInput())
        super().__init__(*args,**kwargs)
        
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result
    
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
    
    product_quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'id': 'stock_quantity',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Stock Quantity'
        }),
        error_messages={
            'required': 'Stock quantity is required',
            'invalid': 'Please enter a valid number',
            'min_value': 'Quantity must be at least 1',
            'max_value': 'Quantity cannot exceed 100'
        },
        min_value=1,
        max_value=100
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
    
    size = forms.ModelChoiceField(
        queryset=Size.objects.all(),
        widget=forms.Select(attrs={
            'id': 'size',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
        }),
        error_messages={
            'required': 'Please select a size',
            'invalid_choice': 'Invalid size selected'
        }
    )
    
    color = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'color',
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100',
            'placeholder': 'Enter Color',
        }),
        required=False
    )

    class Meta:
        model = ProductTable
        fields = ['name', 'description', 'product_quantity', 'base_price', 
                  'sale_Price', 'category', 'size', 'color']

    def clean_product_quantity(self):
        quantity = self.cleaned_data.get('product_quantity')
        if quantity is not None:
            # Convert to string for regex check if needed
            quantity_str = str(quantity)
            
            # Validate quantity
            if quantity < 0:
                raise forms.ValidationError("Quantity cannot be negative")
            if quantity > 100:
                raise forms.ValidationError("Quantity cannot exceed 100 units")
            
            # Optional: If you still want regex validation
            if not re.match(r'^[0-9]+$', quantity_str):
                raise forms.ValidationError("Product Quantity can only contain numbers")
            
            return quantity
        return quantity
    
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
    
class VariantForm(forms.ModelForm):
    size = forms.ModelChoiceField(
        queryset=Size.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-800 border border-gray-600 text-gray-100 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 hover:bg-gray-700 appearance-none',
            'style': 'background-image: url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%23ffffff\' stroke-width=\'2\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' d=\'M19 9l-7 7-7-7\' /%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 1rem center; background-size: 1rem;',
        })
    )

    color = forms.ModelChoiceField(
        queryset=Color.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-100 border border-gray-300 text-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 hover:bg-gray-200 appearance-none',
        })
    )

    class Meta:
        model = VarianceTable
        fields = ['size', 'color', 'Stock_Quantity', 'Price']


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
        required=True,
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
            
            if not re.match(r"^[a-zA-Z0-9\s\-_]+$", category_name):
                raise forms.ValidationError("Category name can only contain letters, numbers, spaces, hyphens, and underscores")
            
            # Check if category name already exists (case-insensitive)
            if Category.objects.filter(category_name__iexact=category_name).exists():
                if self.instance.pk:
                    # Exclude current instance when editing
                    if not Category.objects.filter(category_name__iexact=category_name).filter(pk=self.instance.pk).exists():
                        raise forms.ValidationError("This category name already exists")
                else:
                    raise forms.ValidationError("This category name already exists")
                    
        return category_name

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check file size
            if image.size > 5 * 1024 * 1024:  # 5 MB limit
                raise forms.ValidationError("Image size should not exceed 5 MB")
            
            # Check file type
            valid_types = ['image/jpeg', 'image/png', 'image/gif']
            if image.content_type not in valid_types:
                raise forms.ValidationError("Please upload only JPEG, PNG, or GIF images")
            
        return image