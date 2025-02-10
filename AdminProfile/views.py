from django.shortcuts import render,HttpResponse,redirect,HttpResponseRedirect
from django.contrib import messages 
from AdminProfile.forms import ProductForm,CategoryForm,VariantForm
from AdminProfile.models import Product,Category,ProductTable,VarianceTable,Color,Size,Product_Images_Table
from UserProfile.models import UserTable
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password,check_password #make password for encrypting and check password for decrypting
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
import json


def admin_login(request):
    if request.method == 'POST':
        mail = request.POST.get('email')
        psswrd = request.POST.get('password')
        
        try:
            data = UserTable.objects.get(email=mail)
        except UserTable.DoesNotExist:
            messages.error(request,"Invalid email or password")
            return redirect('admin_login')
        
        if data.is_superuser == False and data.is_staff == False:
            messages.error(request,f"User {data.username} does'nt have an admin permission")
            return redirect('admin_login')
        else:
            if check_password(psswrd, data.password):
                request.session['userMail'] = data.email
                messages.success(request,"Login Successfull")
                return redirect('admin_home')
            else:
                messages.error(request,"Invalid email or password")
                return redirect("admin_login")
        
        if 'userMail' in request.session:
            return redirect('home')
    
    return render(request, 'admin/login.html')            
        
        
   
######################################################################################################################################################################################

def home(request):
    return render(request,'admin/home.html')
        
#############################################################Admin_Users######################################################################################################     

def admin_users(request):
    users = UserTable.objects.all()
    users_per_page = request.GET.get('users_per_page', 5)
    # accessing the query parameter in the url,first is the search query and second is default value returned if key is not found
    search_query = request.GET.get('q','')
    
    if search_query:
        users = UserTable.objects.filter(username__icontains=search_query)
    else:
        users = UserTable.objects.all()
    
    return render(request,'admin/users.html',{'users':users, 'search_query':search_query,'users_per_page':users_per_page}) 

###############################################################################################################################################################################
    
def admin_users_edit(request,user_id):#parameter because to pass to it dynamically
    user = get_object_or_404(UserTable, id=user_id)# dynamic value passed in the url
    #if the object exists,it return the object,
    #or if the objects does not exist, it raises a 404 error.
    
    return render(request,'admin/edit_user.html',{'user':user}) 

########################################################################################################################################################################################

def block_user(request,user_id):
    user = get_object_or_404(UserTable,id = user_id)
    if user.is_active == True:
        user.is_active = False
        user.save()
    return redirect('admin_users')

######################################################################################################################################################################################

def unblock_user(request,user_id):
    user = get_object_or_404(UserTable,id = user_id)
    if user.is_active == False:
        user.is_active = True
        user.save()
    return redirect('admin_users')


################################################################################################################################################################################################################################    

@never_cache
def add_category(request):
    
    # Create a list of existing category names for JavaScript validation
    existing_categories = list(Category.objects.values_list('category_name', flat=True))
    
    if request.method == 'POST':
            form = CategoryForm(request.POST, request.FILES)  # Handle form with request.FILES for image upload
            if form.is_valid():
            
                try:
                    category = form.save()
                    messages.success(request, 'Category added successfully.')
                    return redirect('add_category')  # Redirect to avoid form resubmission
            
                except Exception as e:
                    messages.error(request,f'Error saving category: {str(e)}') 
                
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return redirect('add_category')
    else:    
        form = CategoryForm()
        
        # Get existing products for the template
    existing_categories = [cat.lower() for cat in existing_categories]
    
    context = {
        'form': form,
        'existing_categories': json.dumps(existing_categories)
    }
        
    return render(request, 'admin/add_category.html',context) 

##############################################################################################################################################################################

def category(request):
    categories = Category.objects.all()
    categories_per_page = request.GET.get('categories_per_page', 5)
    
    search_query = request.GET.get('q','')
    
    if search_query:
        categories = Category.objects.filter(category_name__icontains=search_query)
    else:
        categories = Category.objects.all() 
            
    return render(request,'admin/category.html',{'categories':categories, 'search_query':search_query,'categories_per_page':categories_per_page})

###############################################################################################################################################################################

def view_category(request,category_id):
    category = get_object_or_404(Category, id=category_id)
    

    return render(request,'admin/view_category.html',{'category':category})    


#############################################################Product#######################################################################
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from .forms import ProductForm
from .models import ProductTable, VarianceTable, Color, Product_Images_Table
import json

def add_products(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Check if product already exists
                    product_name = form.cleaned_data.get('name')
                    if ProductTable.objects.filter(name__iexact=product_name).exists():
                        messages.error(request, f'Product "{product_name}" already exists')
                        return render(request, 'admin/add-product.html', {
                            'form': form,
                            'existing_products': json.dumps(list(ProductTable.objects.values_list('name', flat=True)))
                        })
                    
                    # Save the product
                    product = form.save()
                    
                    # Handle product images
                    files = request.FILES.getlist('product_images')
                    if not files:
                        messages.warning(request, 'No product images were uploaded')
                    
                    for file in files:
                        if file.content_type.startswith('image'):
                            if file.size <= 5 * 1024 * 1024:  # 5MB limit
                                Product_Images_Table.objects.create(
                                    product=product,
                                    image=file
                                )
                            else:
                                raise ValidationError(f'Image {file.name} exceeds 5MB size limit')
                        else:
                            raise ValidationError(f'File {file.name} is not a valid image')
                    
                    # Handle color
                    color_name = form.cleaned_data.get('color')
                    color_obj = None
                    if color_name:
                        color_obj, _ = Color.objects.get_or_create(color=color_name.strip())
                    
                    # Create variance entry
                    VarianceTable.objects.create(
                        product=product,
                        size=form.cleaned_data['size'],
                        color=color_obj,
                        Stock_Quantity=form.cleaned_data['product_quantity'],
                        Price=form.cleaned_data['base_price']
                    )
                    
                    # Update category total products
                    category = product.category
                    if category:
                        category.total_products = category.products.count()
                        category.save()
                    
                    messages.success(request, f'Product "{product_name}" added successfully')
                    return redirect('products')  # Make sure this URL name exists
                    
            except ValidationError as e:
                messages.error(request, str(e))
                transaction.set_rollback(True)
            except Exception as e:
                messages.error(request, f'Error saving product: {str(e)}')
                transaction.set_rollback(True)
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm()
    
    # Get existing products for the template
    try:
        existing_products = list(ProductTable.objects.values_list('name', flat=True))
    except Exception as e:
        existing_products = []
        messages.error(request, f'Error fetching existing products: {str(e)}')
    
    context = {
        'form': form,
        'existing_products': json.dumps(existing_products),
        'title': 'Add Product'  # For template title
    }
    
    return render(request, 'admin/add-product.html', context)
#########################################################################################Products##############################################################################


def products(request):
    products = ProductTable.objects.select_related('category').prefetch_related(
        'variancetable_set__size',
        'variancetable_set__color'
    )
    
    search_query = request.GET.get('q','')
    
    if search_query:
        products = ProductTable.objects.filter(name__icontains=search_query)
        
    else:
        products = ProductTable.objects.all() 
    
    return render(request,'admin/products.html',{'products':products, 'search_query':search_query})


###############################################################################################################################################################################

def product_detail(request, product_id):
    # Use select_related to fetch related size and color data in a single query
    product = get_object_or_404(ProductTable.objects.select_related('category'), id=product_id)
    variances = VarianceTable.objects.select_related(
        'product',
        'size',
        'color'
    ).filter(product=product)
    

    context = {
        'product': product,
        'variances': variances
    }
    return render(request,'admin/variance.html',context)

##############################################################################################################################################################################    

def variance(request):
    return render(request,'admin/variance.html')

##############################################################################################################################################################################

def edit_product(request):
    return render(request,'admin/edit_product.html')

##############################################################################################################################################################################

def add_variant(request,product_id):
    product = get_object_or_404(ProductTable , id=product_id)
    
    if request.method == 'POST':
        form = VariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.Price = product.sale_Price
            variant.save()
            
            product.product_quantity += variant.Stock_Quantity
            product.save()
            
            return redirect('products')
        
    else:
        form = VariantForm()
    
    return render(request, 'admin/add_variant.html',{'form':form, 'product':product})

###############################################################################################################################################################################