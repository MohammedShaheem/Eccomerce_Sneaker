from django.shortcuts import render,HttpResponse,redirect,HttpResponseRedirect
from django.contrib import messages 
from AdminProfile.forms import ProductForm,CategoryForm,VariantForm,OfferForm,CouponCreationForm
from AdminProfile.models import Product,Category,ProductTable,VarianceTable,Color,Size,Product_Images_Table,Cart,CartItem,OrderItem,Order,Offer,Coupon,ReturnRequest,ReturnRequestItem,Wallet,WalletTransaction
from UserProfile.models import UserTable,Address
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password,check_password #make password for encrypting and check password for decrypting
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
import json
from django.db.models import Sum,F,Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import json
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db.models import Q
from django.core.paginator import Paginator
import os
from decimal import Decimal
from .validators import FormValidator
from django.utils.timezone import now
from datetime import date,datetime, timedelta
from django.db.models import Count
from django.utils import timezone
from.utils import get_allowed_statuses
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff and request.session.get('user_role') == 'admin':
            return redirect('admin_home')
        elif not request.user.is_staff:
            messages.error(request, "Please log out from user side first.")
            return redirect('logout')  # Force logout from user side

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = UserTable.objects.get(email=email)
            
            if not user.is_staff:  # Check if user is not staff
                messages.error(request, f"User {user.username} doesn't have admin permission")
                return render(request, 'admin/login.html')
                
            auth_user = authenticate(username=email, password=password)
                
            if auth_user is not None:
                auth_login(request, auth_user)
                request.session['user_role'] = 'admin'  # Set role as admin
                request.session['userMail'] = email
                messages.success(request, "Login successful")
                return redirect("admin_home")
            
            else:
                if not user.check_password(password):
                    messages.error(request, "Incorrect password")
                else:
                    messages.error(request, "Authentication failed, please try again")
        
        except UserTable.DoesNotExist:
            messages.error(request, "No account found with this email")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            messages.error(request, 'An unexpected error occurred')
    
    return render(request, 'admin/login.html')           
#################################################################################################################################
def admin_logout(request):
    # Clear both authentication and session
    if request.user.is_authenticated:
        auth_logout(request)
    
    if 'userMail' in request.session:
        request.session.flush()  # Clear all session data
    
    messages.success(request, "You have been logged out successfully.")
    return redirect('admin_login')        
        
   
######################################################################################################################################################################################
def get_sales_data(time_filter='month'):
    now = timezone.now()
    
    if time_filter == 'week':
        # last 7 days
        start_date = now - timedelta(days=7)
        date_format = '%d %b'  # Consistent format
        query_format = "DATE(ordered_date)"
        
    elif time_filter == 'month':
        # last 30 days
        start_date = now - timedelta(days=30)
        date_format = '%d %b'  # Consistent format
        query_format = "DATE(ordered_date)"
        
    elif time_filter == 'year':
        # last 12 months
        start_date = now - timedelta(days=365)
        date_format = '%b %y'  # Month-Year format
        query_format = "TO_CHAR(ordered_date, 'YY-MM')"
        
    else:
        # default month
        start_date = now - timedelta(days=30)
        date_format = '%d %b'  # Consistent format
        query_format = "DATE(ordered_date)"
    
    # getting the sales data by date
    orders = Order.objects.filter(
        ordered_date__gte=start_date,
        order_status__in=['DELIVERED','SHIPPED','PROCESSING']
    ).extra(
        select={'date': query_format}
    ).values('date').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('date')
    
    # formatting date for the chart
    labels = []
    sales_values = []
    order_counts = []
    
    for entry in orders:
        if time_filter == 'year':
            # For year, entry['date'] should be in format 'YY-MM'
            if isinstance(entry['date'], str):
                try:
                    date_obj = datetime.strptime(entry['date'], '%y-%m')
                    formatted_date = date_obj.strftime('%b %y')
                except ValueError:
                    # Handle potential format issues
                    formatted_date = entry['date']
            else:
                formatted_date = entry['date'].strftime('%b %y')
        else:
            # For week/month
            if isinstance(entry['date'], str):
                try:
                    # PostgreSQL may return date as string in format 'YYYY-MM-DD'
                    date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d %b')
                except ValueError:
                    formatted_date = entry['date']
            else:
                formatted_date = entry['date'].strftime('%d %b')
        
        labels.append(formatted_date)
        sales_values.append(float(entry['total']))
        order_counts.append(entry['count'])
    
    return {
        'labels': labels,
        'sales': sales_values,
        'orders': order_counts
    }


def get_top_selling_products(limit=10):
    top_products = OrderItem.objects.values(
        'product__name','variant__product__name'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('price_per_item') * F('quantity'))
        
    ).order_by('-total_sold')[:limit]
    
    #formatting the results
    result = []
    for product in top_products:
        name = product.get('product__name') or product.get('variant__product__name')
        if name:
            result.append({
                'name': name,
                'total_sold': product['total_sold'],
                'revenue': float(product['revenue'])
            })
    
    return result

def get_top_selling_categories(limit=10):
    
    #getting orders with product variants
    top_categories = OrderItem.objects.filter(
        variant__product__category__isnull=False
    ).values(
        'variant__product__category__category_name'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('price_per_item') * F('quantity') )
    ).order_by('-total_sold')[:limit]
    
    
    #formating the results
    result = []
    for category in top_categories:
        category_name = category.get('variant__product__category__category_name')
        if category_name:
            result.append({
                'name': category_name,
                'total_sold': category['total_sold'],
                'revenue': float(category['revenue'])
            })
    
    return result



def get_revenue_stats(time_filter='month'):
    now = timezone.now()
    
    
    if time_filter == 'week':
        start_date = now - timedelta(days=7)
        prev_start_date = start_date - timedelta(days=7)
    elif time_filter == 'month':
        start_date = now - timedelta(days=30)
        prev_start_date = start_date - timedelta(days=30)
    elif time_filter == 'year':
        start_date = now - timedelta(days=365)
        prev_start_date = start_date - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
        prev_start_date = start_date - timedelta(days=30)
    
    #getting the current period revenue
    current_revenue = Order.objects.filter(
        ordered_date__gte=start_date,
        order_status__in=['DELIVERED', 'SHIPPED', 'PROCESSING']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    #getting the previous period revenue
    prev_revenue = Order.objects.filter(
        ordered_date__gte=prev_start_date,
        ordered_date__lt=start_date,
        order_status__in=['DELIVERED', 'SHIPPED', 'PROCESSING']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    #calculateing growth percentage
    if prev_revenue > 0:
        growth_percentage = ((current_revenue - prev_revenue) / prev_revenue) * 100
    else:
        growth_percentage = 100 if current_revenue > 0 else 0
    
    return {
        'current_revenue': float(current_revenue),
        'prev_revenue': float(prev_revenue),
        'growth_percentage': round(growth_percentage, 2)
    }


def sales_chart_data(request):
    #for getting sales data
    time_filter = request.GET.get('time_filter', 'month')
    data = get_sales_data(time_filter)
    return JsonResponse(data)
    




from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

@login_required
def admin_home(request):
    # Get filter parameters
    time_filter = request.GET.get('time_filter', 'month')
    
    # Determine start_date based on time_filter (consistent with get_sales_data)
    now = timezone.now()
    if time_filter == 'week':
        start_date = now - timedelta(days=7)
    elif time_filter == 'month':
        start_date = now - timedelta(days=30)
    elif time_filter == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    # Get dashboard data
    sales_data = get_sales_data(time_filter)
    top_products = get_top_selling_products()
    top_categories = get_top_selling_categories()
    revenue_stats = get_revenue_stats(time_filter)
    
    # Calculate totals
    total_sales = sum(sales_data['sales']) if sales_data['sales'] else 0
    # Total orders (all statuses)
    total_orders = Order.objects.filter(
        ordered_date__gte=start_date
    ).count()
    # Total active orders (for avg_order_value, matching sales_data)
    total_active_orders = sum(sales_data['orders']) if sales_data['orders'] else 0
    avg_order_value = total_sales / total_active_orders if total_active_orders > 0 else 0
    
    context = {
        'sales_data': sales_data,
        'top_products': top_products,
        'top_categories': top_categories,
        'revenue_stats': revenue_stats,
        'time_filter': time_filter,
        'total_orders': total_orders,  # Add this to context
        'avg_order_value': avg_order_value,
    }
    
    return render(request, 'admin/home.html', context)
        
#############################################################Admin_Users######################################################################################################     
@login_required
def admin_users(request):
    # Fetch all users
    users = UserTable.objects.all()
    
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Apply search filter if query exists
    if search_query:
        users = UserTable.objects.filter(username__icontains=search_query)
    
    # Pagination
    users_per_page = request.GET.get('users_per_page', 4)  # Default to 4 users per page
    paginator = Paginator(users, int(users_per_page))
    page = request.GET.get('page', 1)
    
    try:
        paginated_users = paginator.page(page)
    except PageNotAnInteger:
        paginated_users = paginator.page(1)
    except EmptyPage:
        paginated_users = paginator.page(paginator.num_pages)
    
    return render(request, 'admin/users.html', {
        'users': paginated_users,  # Pass paginated users
        'search_query': search_query,
        'users_per_page': users_per_page
    })

###############################################################################################################################################################################
@login_required
def admin_users_edit(request,user_id):#parameter because to pass to it dynamically
    user = get_object_or_404(UserTable, id=user_id)# dynamic value passed in the url
    #if the object exists,it return the object,
    #or if the objects does not exist, it raises a 404 error.
    default_address = user.addresses.filter(is_default=True).first()
    
    return render(request,'admin/edit_user.html',{'user':user,'default_address': default_address,}) 

########################################################################################################################################################################################
@login_required
def block_user(request,user_id):
    user = get_object_or_404(UserTable,id = user_id)
    if user.is_active == True:
        user.is_active = False
        user.save()
    return redirect('admin_users')

######################################################################################################################################################################################
@login_required
def unblock_user(request,user_id):
    user = get_object_or_404(UserTable,id = user_id)
    if user.is_active == False:
        user.is_active = True
        user.save()
    return redirect('admin_users')


################################################################################################################################################################################################################################    
@login_required
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
                    return redirect('category')  # Redirect to avoid form resubmission
            
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
from django.db.models import Exists, OuterRef
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.db.models import Exists, OuterRef
from .models import Category, Offer
from datetime import date

@login_required
def category(request):
    today = date.today()
    
    
    active_offers = Offer.objects.filter(
        category=OuterRef('pk'),
        is_active=True,
        valid_from__lte=today,
        valid_till__gte=today
    )
    
    
    search_query = request.GET.get('q', '')
    categories = Category.objects.prefetch_related('offers').annotate(
        has_active_offer=Exists(active_offers)
    )
    
    if search_query:
        categories = categories.filter(category_name__icontains=search_query)
    
    
    for cat in categories:
        if cat.has_active_offer:
            print(f"Category: {cat.category_name}, Has Active Offer: {cat.has_active_offer}")
    
    # Pagination
    categories_per_page = request.GET.get('categories_per_page', 5)
    paginator = Paginator(categories, int(categories_per_page))
    page = request.GET.get('page', 1)
    
    try:
        paginated_categories = paginator.page(page)
    except PageNotAnInteger:
        paginated_categories = paginator.page(1)
    except EmptyPage:
        paginated_categories = paginator.page(paginator.num_pages)
    
    context = {
        'categories': paginated_categories,
        'search_query': search_query,
        'categories_per_page': categories_per_page
    }
    
    return render(request, 'admin/category.html', context)
            
    

###############################################################################################################################################################################
@login_required
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
@login_required
def add_products(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        
        if form.is_valid():
                try:
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
                    
                    # Update category total products
                    category = product.category
                    if category:
                        category.total_products = category.products.count()
                        category.save()
                    
                    messages.success(request, f'Product "{product_name}" added successfully')
                    return redirect('products')  # Make sure this URL name exists
                    
                except ValidationError as e:
                    messages.error(request, str(e))
                
                except Exception as e:
                    messages.error(request, f'Error saving product: {str(e)}')
                
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
        'title': 'Add Product' 
    }
    
    return render(request, 'admin/add-product.html', context)
#########################################################################################Products##############################################################################

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from .models import ProductTable

def products(request):
    today = date.today()
    
    # Subquery to check for active offers
    active_offers = Offer.objects.filter(
        product=OuterRef('pk'),
        is_active=True,
        valid_from__lte=today,
        valid_till__gte=today
    )
    
    # Base queryset with annotation
    products = ProductTable.objects.select_related('category').prefetch_related(
        'variances',
        'variances__size',  
        'variances__color',
    ).filter(Is_deleted=False).annotate(
        has_active_offer=Exists(active_offers)
    )
    
    # Apply search query
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Debugging: Print products with active offers
    for prod in products:
        if prod.has_active_offer:
            print(f"Product: {prod.name}, Has Active Offer: {prod.has_active_offer}")
    
    # Pagination
    products_per_page = request.GET.get('products_per_page', 4)
    paginator = Paginator(products, int(products_per_page))
    page = request.GET.get('page', 1)
    
    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)
    
    return render(request, 'admin/products.html', {
        'products': paginated_products, 
        'search_query': search_query,
        'products_per_page': products_per_page
    })

###############################################################################################################################################################################
@login_required
def product_detail(request, product_id):
    #use ingselect_related to fetch related size and color data in a single query
    product = get_object_or_404(ProductTable.objects.select_related('category'), id=product_id)
    variances = VarianceTable.objects.select_related(
        'product',
        'size',
        'color'
    ).filter(product=product)
    
    search_query = request.GET.get('q', '')
    
    if search_query:
        variances = variances.filter(
        Q(size__size__icontains=search_query) |
        Q(color__color__icontains=search_query)
    )
        
    else:
        variances = VarianceTable.objects.filter(product=product)
        
    
    # Pagination
    variances_per_page = int(request.GET.get('variances_per_page', 4))  
    paginator = Paginator(variances, variances_per_page)  
    page = request.GET.get('page', 1)
    
    try:
        paginated_variances = paginator.page(page)
    except PageNotAnInteger:
        paginated_variances = paginator.page(1)
    except EmptyPage:
        paginated_variances = paginator.page(paginator.num_pages)
    
    
    context = {
        'product': product,
        'variances': paginated_variances,  
        'search_query': search_query,
    }
    
    return render(request, 'admin/variance.html', context)

##############################################################################################################################################################################    
@login_required
def variance(request):
    return render(request,'admin/variance.html')

##############################################################################################################################################################################
@login_required
def edit_product(request):
    return render(request,'admin/edit_product.html')

##############################################################################################################################################################################
@login_required
def add_variant(request, product_id):
    product = get_object_or_404(ProductTable, id=product_id)
    
    if request.method == 'POST':
        form = VariantForm(request.POST, request.FILES)
        
        # Handle color
        color_name = request.POST.get('color', '').strip()
        color_obj = None
        
        if color_name:
            try:    
                # First try to get existing color
                color_obj = Color.objects.filter(color=color_name).first()
                if not color_obj:
                    # If color doesn't exist, create and save it
                    color_obj = Color.objects.create(color=color_name)
            except Exception as e:
                messages.error(request, f"Error processing color: {str(e)}")
                return render(request, 'admin/add_variant.html', {
                    'form': form,
                    'product': product,
                    'existing_images': Product_Images_Table.objects.filter(product=product)
                })
        
        if form.is_valid():
            try:
                # Only check for existing variant if we have both color and size
                if color_obj and form.cleaned_data['size']:
                    existing_variant = VarianceTable.objects.filter(
                        product=product,
                        size=form.cleaned_data['size'],
                        color=color_obj
                    ).first()
                    
                    if existing_variant:
                        messages.error(request, "A variant with this size and color combination already exists.")
                        return render(request, 'admin/add_variant.html', {
                            'form': form, 
                            'product': product,
                            'existing_images': Product_Images_Table.objects.filter(product=product)
                        })
                
                # Create new variant
                variant = form.save(commit=False)
                variant.product = product
                variant.color = color_obj
                variant.save()
                
                # Handle variant-specific images
                images = request.FILES.getlist('images')
                if images:
                    for image in images:
                        Product_Images_Table.objects.create(
                            variant=variant,
                            image=image
                        )
                
                # Update product quantity
                product.product_quantity = (
                    VarianceTable.objects.filter(product=product)
                    .aggregate(total_quantity=Sum('Stock_Quantity'))
                    ['total_quantity'] or 0
                )
                product.save()
                
                # Update category total products
                category = product.category
                if category:
                    category.total_products = (
                        ProductTable.objects.filter(category=category)
                        .aggregate(total_quantity=Sum('product_quantity'))
                        ['total_quantity'] or 0
                    )
                    category.save()
                
                # Success message
                success_message = "Variant added successfully"
                if images:
                    success_message += f" with {len(images)} image{'s' if len(images) > 1 else ''}"
                messages.success(request, success_message)
                
                return redirect('products')
                
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, 'admin/add_variant.html', {
                    'form': form, 
                    'product': product,
                   'existing_images': Product_Images_Table.objects.filter(variant__product=product)  # Using double underscore to follow the relationship
                })
            
            except Exception as e:
                messages.error(request, f"Error saving variant: {str(e)}")
                return render(request, 'admin/add_variant.html', {
                    'form': form, 
                    'product': product,
                    'existing_images': Product_Images_Table.objects.filter(variant__product=product)  # Using double underscore to follow the relationship
                })
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = VariantForm()
    
    context = {
        'form': form,
        'product': product,
        'existing_images': Product_Images_Table.objects.filter(variant__product=product)  # Using double underscore to follow the relationship
        
    }
    
    return render(request, 'admin/add_variant.html', context)
############################################################################################################################################################################### 
@login_required
def single_product_view(request, variance_id):
    # Get the current variance with related fields
    variance = get_object_or_404(VarianceTable.objects.select_related(
        'size',
        'color'
    ).prefetch_related('images'), id=variance_id)
    
    # Get all variances for the same product to show options
    related_variances = VarianceTable.objects.filter(
        product=variance.product
    ).select_related('size', 'color').exclude(id=variance_id)
    
    # Get all unique colors and sizes for this product's variances
    available_colors = VarianceTable.objects.filter(
        product=variance.product
    ).values_list('color__color', flat=True).distinct()
    
    available_sizes = VarianceTable.objects.filter(
        product=variance.product
    ).values_list('size__size', flat=True).distinct()
    
    
    
    context = {
        'variance': variance,
        'related_variances': related_variances,
        'available_colors': available_colors,
        'available_sizes': available_sizes,
        
    }
    
    return render(request, 'admin/single_product_view.html', context)

########################################################################################################################################################################################
@login_required
@never_cache
def edit_category(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        messages.error(request, 'Category not found')
        return redirect('category')
    
    #creating a list of existing category names for  validation (excluding this category)
    existing_categories = list(Category.objects.exclude(id=category_id).values_list('category_name', flat=True))
    existing_categories = [cat.lower() for cat in existing_categories]
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        valid_data = True  #flag to track if all validations pass
        
        try:
            #validating category name
            category_name = request.POST.get('category_name', '').strip()
            
            if not category_name:
                messages.error(request, 'Category name is required')
                valid_data = False
            
            if len(category_name) < 3:
                messages.error(request, 'Category name must be at least 3 characters long')
                valid_data = False
            
            if len(category_name) > 20:
                messages.error(request, 'Category name must be less than 20 characters')
                valid_data = False
            
            #checking to existing category name
            if category_name.lower() in existing_categories:
                messages.error(request, "Category name already exists")
                valid_data = False
            
            #validating description
            description = request.POST.get('description', '').strip()
            if not description:
                messages.error(request, 'Description is required')
                valid_data = False
            
            if len(description) < 10:
                messages.error(request, 'Description must be at least 10 characters long')
                valid_data = False
            
            if len(description) > 200:
                messages.error(request, 'Description must be less than 200 characters')
                valid_data = False
            
            #validating image if a new one is uploaded
            if 'image' in request.FILES:
                image = request.FILES['image']
                print(f"image:{image}")
                
                #validateing file size 
                if image.size > 2 * 1024 * 1024:
                    messages.error(request, 'Image size should be less than 2MB')
                    valid_data = False
                
                #validateing file extension
                allowed_extensions = ['jpg', 'jpeg', 'png']
                ext = image.name.split('.')[-1].lower()
                if ext not in allowed_extensions:
                    messages.error(request, f'Only {", ".join(allowed_extensions)} files are allowed')
                    valid_data = False
            
            
            if valid_data:
                #deleteing old image if new one is uploaded
                if 'image' in request.FILES and category.image:
                    if os.path.isfile(category.image.path):
                        os.remove(category.image.path)
                
                #updateing category fields
                category.category_name = category_name
                category.description = description
                if 'image' in request.FILES:
                    category.image = request.FILES['image']
                
                
                category.status = request.POST.get('status') == 'on'
                
                #saveing the category
                category.save()
                messages.success(request, 'Category updated successfully')
                return redirect('category')
                
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'existing_categories': json.dumps(existing_categories)
    }
    
    return render(request, 'admin/edit_category.html', context)

@login_required
@never_cache
def block_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        print(f"Blocking category. Current status: {category.status}")
        category.status = False
        category.save()
        print(f"New status after blocking: {category.status}")
        messages.success(request, 'Category unlisted successfully')
    return redirect('edit_category', category_id=category_id)

@login_required
@never_cache
def unblock_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        print(f"Unblocking category. Current status: {category.status}")
        category.status = True
        category.save()
        print(f"New status after unblocking: {category.status}")
        messages.success(request, 'Category listed successfully')
    return redirect('edit_category', category_id=category_id)
 
################################################################################################################################################################################
@login_required
def edit_product(request, product_id):
    try:
        product = get_object_or_404(ProductTable, id=product_id, Is_deleted = False)
        variance = VarianceTable.objects.filter(product=product).first()
        product_images = variance.images.all()
        
        
        
        if request.method == 'POST':
            if 'delete_product' in request.POST:
                return redirect('delete_product', product_id=product_id)
        
        
        if request.method == 'POST':
            #creating an copy of POST data that for modifying
            post_data = request.POST.copy()
            
            #preserving the orginal category,color,and size values
            if product.category:
                post_data['category'] = product.category.id
                
            if variance and variance.color:
                post_data['color'] = variance.color.color
                
            if variance and variance.size:
                post_data['size'] = variance.size.id
                
            if product.product_quantity:
                post_data['product_quantity'] = product.product_quantity
                
            form = ProductForm(post_data, request.FILES, instance=product)
            
            #initializing the validator
            validator = FormValidator()
            
            
            #validate product fields
            validator.validate_text_field(
                post_data.get('name'),
                'Product name',
                min_length=3,
                max_length=100,
                pattern="^[a-zA-Z0-9\s\-_]+$"
            )
            
            validator.validate_text_field(
                post_data.get('description'),
                'Product description',
                min_length=10,
                max_length=2000
            )
            
            validator.validate_decimal(
                post_data.get('base_price'),
                'Base price',
                min_value=Decimal('0.01'),
                max_value=Decimal('999999.99')
            )
            
            
            if post_data.get('sale_Price'):
                validator.validate_decimal(
                    post_data.get('sale_Price'),
                    'Sale price',
                    required=False,
                    max_value=Decimal(post_data.get('base_price', '0')) - Decimal('0.01')
                )
            
            #validating the new image
            for image in request.FILES.getlist('product_images'):
                validator.validate_file(
                    image,
                    f'Image {image.name}',
                    required=False,
                    allowed_types=['image'],
                    allowed_extensions = ['jpg', 'jpeg', 'png','avif'],
                    max_size=5 * 1024 * 1024
                )
            
            
            #checking for validation error
            validation_errors = validator.get_errors()
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)
                return render(request, 'admin/edit_product.html', {
                    'form': form,
                    'product': product,
                    'product_images': product_images,
                    'existing_products': json.dumps(list(ProductTable.objects.exclude(id=product_id).values_list('name', flat=True)))
                })
                        
            
            if form.is_valid():
                try:
                    #checking hte product name exist not for this product
                    product_name = form.cleaned_data.get('name')
                    if ProductTable.objects.filter(name__iexact=product_name).exclude(id=product_id).exists():
                         messages.error(request, f'Product "{product_name}" already exists')
                         return render(request, 'admin/edit_product.html', {
                                'form': form,
                                'product': product,
                                'product_images': product_images,
                                'existing_products': json.dumps(list(ProductTable.objects.exclude(id=product_id).values_list('name', flat=True)))
                            })
                    
                    
                    #saving the product
                    updated_product = form.save()
                    
                    #handiling product images
                    files = request.FILES.getlist('product_images')
                    
                    images_to_delete = request.POST.getlist('delete_images')
                    if images_to_delete:
                        Product_Images_Table.objects.filter(id__in=images_to_delete).delete()
                        
                    
                    # Handle new images
                    for file in request.FILES.getlist('product_images'):
                        Product_Images_Table.objects.create(
                            product=updated_product,
                            image=file
                            )
                        
                    #updating the price in variance
                    if variance:
                        variance.Price = form.cleaned_data['base_price']
                        variance.save()
                            
                    messages.success(request, f'Product "{product_name}" updated successfully')
                    return redirect('products')  
                        
                except Exception as e:
                    messages.error(request, f'Error updating product: {str(e)}')
                    
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            # GET request - populate form with existing data
            initial_data = {
                'name': product.name,
                'description': product.description,
                'base_price': product.base_price,
                'sale_Price': product.sale_Price,
            }
            form = ProductForm(initial=initial_data, instance=product)
        
        context = {
            'form': form,
            'product': product,
            'product_images': product_images,
            'existing_products': json.dumps(list(ProductTable.objects.exclude(id=product_id).values_list('name', flat=True))),
            'title': 'Edit Product'
        }
        
        return render(request, 'admin/edit_product.html', context)
    
    except ProductTable.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('products')
    
############################################################################################################################################

@login_required
def edit_variant(request, variant_id):
    variant = get_object_or_404(VarianceTable, id=variant_id)
    product = variant.product
    
    if request.method == 'POST':
        form = VariantForm(request.POST, request.FILES, instance=variant)
        
        # Handle color
        color_name = request.POST.get('color', '').strip()
        color_obj = None
        
        if color_name:
            try:
                # First try to get existing color
                color_obj = Color.objects.filter(color=color_name).first()
                if not color_obj:
                    # If color doesn't exist, create and save it
                    color_obj = Color.objects.create(color=color_name)
            except Exception as e:
                messages.error(request, f"Error processing color: {str(e)}")
                return render(request, 'admin/edit_variant.html', {
                    'form': form,
                    'variant': variant,
                    'product': product,
                    'existing_images': Product_Images_Table.objects.filter(variant=variant)
                })
        
        if form.is_valid():
            try:
                # Check for existing variant with same color and size (excluding current variant)
                if color_obj and form.cleaned_data['size']:
                    existing_variant = VarianceTable.objects.filter(
                        product=product,
                        size=form.cleaned_data['size'],
                        color=color_obj
                    ).exclude(id=variant_id).first()
                    
                    if existing_variant:
                        messages.error(request, "A variant with this size and color combination already exists.")
                        return render(request, 'admin/edit_variant.html', {
                            'form': form,
                            'variant': variant,
                            'product': product,
                            'existing_images': Product_Images_Table.objects.filter(variant=variant)
                        })
                
                # Update variant
                updated_variant = form.save(commit=False)
                updated_variant.color = color_obj
                updated_variant.save()
                
                # Handle image deletion
                images_to_delete = request.POST.getlist('delete_images')
                current_images = Product_Images_Table.objects.filter(variant=variant)
                
                # Ensure at least one image remains
                if len(images_to_delete) >= current_images.count():
                    messages.error(request, "Cannot delete all images. At least one image must remain.")
                else:
                    Product_Images_Table.objects.filter(id__in=images_to_delete).delete()
                
                # Handle new images
                new_images = request.FILES.getlist('images')
                if new_images:
                    for image in new_images:
                        Product_Images_Table.objects.create(
                            variant=variant,
                            image=image
                        )
                
                # Update product quantity
                product.product_quantity = (
                    VarianceTable.objects.filter(product=product)
                    .aggregate(total_quantity=Sum('Stock_Quantity'))
                    ['total_quantity'] or 0
                )
                product.save()
                
                # Update category total products
                if product.category:
                    product.category.total_products = (
                        ProductTable.objects.filter(category=product.category)
                        .aggregate(total_quantity=Sum('product_quantity'))
                        ['total_quantity'] or 0
                    )
                    product.category.save()
                
                messages.success(request, "Variant updated successfully")
                return redirect('products')
                
            except Exception as e:
                messages.error(request, f"Error updating variant: {str(e)}")
                
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        # Initialize form with current variant data
        initial_data = {
            'size': variant.size,
            'Stock_Quantity': variant.Stock_Quantity,
        }
        if variant.color:
            initial_data['color'] = variant.color.color
            
        form = VariantForm(initial=initial_data, instance=variant)
    
    context = {
        'form': form,
        'variant': variant,
        'product': product,
        'existing_images': Product_Images_Table.objects.filter(variant=variant)
    }
    
    return render(request, 'admin/edit_variant.html', context)
                






def toggle_product_status(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(ProductTable, id=product_id)
        product.Is_active = not product.Is_active
        product.save()
        
        status = "unblocked" if product.Is_active else "blocked"
        messages.success(request, f"Product '{product.name}' has been {status} successfully.")
        
        return redirect('edit_product', product_id=product_id)
    return redirect('products')

@login_required
def delete_product(request, product_id):
    try:
        product = get_object_or_404(ProductTable, id=product_id, Is_deleted=False)
        
        if request.method == 'POST':
            #soft delete the product
            product.Is_deleted = True
            product.save()
            
            #updating category total product count 
            if product.category:
                category = product.category
                category.total_products = category.products.filter(Is_deleted=False).count()
                category.save()
                
            messages.success(request, f"Product {product.name} hasbeen deleted successfully")
            return redirect ('products')
        
        return render(request, 'admin/delete_product_confirm.html',{
            'product':product,
            'title':'Delete Product'
        })
    
    except ProductTable.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('products')
    



@login_required
def admin_orders(request):
    # Getting the filter parameters from request
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')
    search_query = request.GET.get('search', '')
    
    # Optimize query with select_related and prefetch_related
    orders = Order.objects.all().select_related('user', 'order_address').prefetch_related('items', 'items__variant', 'items__product').order_by('-ordered_date')
    
    # Applying filters
    if status_filter:
        orders = orders.filter(order_status=status_filter)
        
        
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
        
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(items__product__name__icontains=search_query)
        ).distinct()
    
    # Getting counts for summary cards
    pending_payment_count = Order.objects.filter(payment_status='PENDING').count()
    processing_count = Order.objects.filter(order_status='PROCESSING').count()
    delivered_count = Order.objects.filter(order_status='DELIVERED').count()
    canceled_count = Order.objects.filter(order_status='CANCELED').count()
    
    # For pagination
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_orders': paginator.count,
        'pending_payment_count': pending_payment_count,
        'processing_count': processing_count,
        'delivered_count': delivered_count,
        'canceled_count': canceled_count,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search_query': search_query,
        'Order': Order,
    }
    
    return render(request, 'admin/admin_orders.html', context)


@login_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related(
        'user', 
        'order_address'
    ).prefetch_related(
        'items',
        'items__variant',
        'items__product'
    ), order_id=order_id)
    
    has_pending_return_requests = ReturnRequest.objects.filter(order=order, status='REQUESTED').exists()
    
    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            if order.order_status == 'RETURNED':
                messages.error(request, "Order has already been returned. No further status changes allowed.")
                return redirect('admin_order_detail', order_id=order_id)
            
            if new_status == 'RETURNED':
                messages.error(request, "Order status cannot be directly changed to RETURNED. Approve a return request instead.")
                return redirect('admin_order_detail', order_id=order_id)
            
            
            if order.order_status == 'PENDING' and new_status not in ['PROCESSING', 'DELIVERED']:
                messages.error(request, 'From "PENDING", order can only be changed to "PROCESSING" or "DELIVERED".')
                return redirect('admin_order_detail', order_id=order_id)

            
            if has_pending_return_requests:
                messages.error(request, 'Cannot update status manually while there are pending return requests.')
                return redirect('admin_order_detail', order_id=order_id)
            
            order.order_status = new_status
            order.payment_status = 'PAID'
            order.save()
            
            
            if new_status == 'CANCELED':
                pass  # Add cancellation logic if needed
            else:
                order.items.filter(is_returned=False).update(
                    item_status=new_status,
                    item_payment_status=new_status
                )
            
            messages.success(request, "Order status updated successfully.")
            return redirect('admin_order_detail', order_id=order_id)
    
    context = {
        'order': order,
        'Order': Order,
        'has_pending_return_requests': has_pending_return_requests,
        'allowed_statuses': get_allowed_statuses(order),
    }
    return render(request, 'admin/order_detail.html', context)

##########################################################################################################################################################################################################################


def admin_return_requests(request):
    return_requests = ReturnRequest.objects.all().order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter:
        return_requests = return_requests.filter(status=status_filter)
        
    # Pagination
    paginator = Paginator(return_requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'pending_count': ReturnRequest.objects.filter(status='REQUESTED').count(),
        'approved_count': ReturnRequest.objects.filter(status='APPROVED').count(),
        'rejected_count': ReturnRequest.objects.filter(status='REJECTED').count(),
    }
    
    return render(request, 'admin/return_requests.html', context)

@login_required
def admin_return_request_detail(request, request_id):
    return_request = get_object_or_404(ReturnRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        try:
            with transaction.atomic():
                if action == 'approve':
                    return_request.status = 'APPROVED'
                    return_request.admin_notes = admin_notes
                    return_request.save()
                    
                    order = return_request.order
                    return_items = return_request.items.all()
                    total_refund = Decimal('0.00')
                    
                    for return_item in return_items:
                        order_item = return_item.order_item
                        order_item.is_returned = True
                        order_item.return_date = timezone.now()
                        order_item.return_reason = return_request.reason
                        order_item.item_status = 'RETURNED'
                        order_item.save()
                        
                        item_refund = order_item.total_amount
                        total_refund += item_refund
                        print(f"Item: {order_item}, Refund Amount: {item_refund}, Running Total: {total_refund}")
                    
                    all_items_returned = all(item.is_returned for item in order.items.all())
                    
                    if all_items_returned:
                        order.order_status = 'RETURNED'
                        order.return_status = 'APPROVED'
                        order.payment_status = 'REFUNDED'
                    else:
                        order.order_status = 'PARTIALLY_RETURNED'
                        order.return_status = 'PARTIALLY_APPROVED'
                        order.payment_status = 'PARTIALLY_REFUNDED'
                    
                    total_refund = max(total_refund, Decimal('0.00'))
                    order.refund_amount = (order.refund_amount or Decimal('0.00')) + total_refund
                    order.return_date = timezone.now()
                    order.refund_date = timezone.now()
                    order.save()
                    
                    if hasattr(return_request.user, 'wallet') and return_request.user.wallet:
                        return_request.user.wallet.credit(
                            amount=total_refund,
                            description=f"Refund for returned item(s) from order #{order.order_id}",
                            order=order,
                            transaction_category='ORDER_RETURN'
                        )
                        messages.success(request, f'Return request approved and ₹{total_refund} has been refunded to customer wallet')
                    else:
                        messages.error(request, 'User wallet not found. Refund not processed.')
                        
                elif action == 'reject':
                    return_request.status = 'REJECTED'
                    return_request.admin_notes = admin_notes
                    return_request.save()
                    
                    order = return_request.order
                    order.return_status = 'REJECTED'
                    order.save()
                    
                    messages.success(request, 'Return request rejected')
                
                else:
                    messages.error(request, 'Invalid action')
                
                return redirect('admin_return_request_detail', request_id=request_id)
        
        except Exception as e:
            messages.error(request, f'Error processing action: {str(e)}')
            import traceback
            print(traceback.format_exc())
    
    return_items = return_request.items.all()
    total_refund_amount = Decimal('0.00')
    for item in return_items:
        total_refund_amount += item.order_item.total_amount
    
    # Check for pending return requests
    has_pending_return_requests = ReturnRequest.objects.filter(
        order=return_request.order, 
        status='REQUESTED'
    ).exists()
    
    context = {
        'return_request': return_request,
        'return_items': return_items,
        'total_refund_amount': total_refund_amount,
        'has_pending_return_requests': has_pending_return_requests,  # Added context variable
    }
    
    return render(request, 'admin/return_request_detail.html', context)


from django.db import models

@login_required
def offer_list(request):
    product_offers = Offer.objects.filter(offer_type = 'product').order_by('-created_at')
    category_offers = Offer.objects.filter(offer_type = 'category').order_by('-created_at')
    
    context = {
        'product_offers':product_offers,
        'category_offers':category_offers
    }
    
    return render(request, 'admin/offer_list.html',context)

def add_offer(request, source, source_id):
    if source not in ['product', 'category']:
        messages.error(request, 'Invalid source type')
        return redirect('offer_list')

    try:
        if source == 'product':
            source_obj = ProductTable.objects.get(id=source_id, Is_deleted=False)
            initial_data = {'offer_type': 'product', 'product': source_obj.id}
            lowest_price = None  # Not needed for product offers
        else:
            source_obj = Category.objects.get(id=source_id, is_delete=False)
            initial_data = {'offer_type': 'category', 'category': source_obj.id}
            # Get the lowest price for category validation
            lowest_price = ProductTable.objects.filter(
                category=source_obj,
                Is_deleted=False,
                Is_active=True
            ).aggregate(min_price=models.Min('sale_Price'))['min_price']
            lowest_price = float(lowest_price) if lowest_price is not None else None
    except (ProductTable.DoesNotExist, Category.DoesNotExist):
        messages.error(request, f'{source.title()} not found')
        return redirect('offer_list')

    if request.method == 'POST':
        print("POST data:", request.POST)
        form = OfferForm(request.POST, offer_type=source)
        if form.is_valid():
            print("Form is valid")
            try:
                offer = form.save(commit=False)
                offer.offer_type = source
                if source == 'product':
                    offer.product = source_obj
                else:
                    offer.category = source_obj

                existing_offer = Offer.objects.filter(
                    **{source: source_obj},
                    is_active=True,
                    valid_till__gte=timezone.now()
                ).exists()

                if existing_offer:
                    messages.error(request, f'An active offer already exists for this {source}')
                    return render(request, 'admin/offer_form.html', {
                        'form': form,
                        'source_type': source,
                        'source_obj': source_obj,
                        'is_edit': False,
                        'lowest_price': lowest_price
                    })

                offer.save()
                messages.success(request, 'Offer added successfully')
                return redirect('offer_list')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = OfferForm(initial=initial_data, offer_type=source)

    context = {
        'form': form,
        'source_type': source,
        'source_obj': source_obj,
        'is_edit': False,
        'lowest_price': lowest_price  
    }
    return render(request, 'admin/offer_form.html', context)

def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    
    if request.method == 'POST':
        form = OfferForm(
            request.POST,
            instance=offer,
            offer_type=offer.offer_type
        )
        if form.is_valid():
            try:
                offer = form.save(commit=False)
                
                # Check for existing active offers (excluding current offer)
                existing_offer = Offer.objects.filter(
                    Q(product=offer.product) if offer.offer_type == 'product' 
                    else Q(category=offer.category),
                    is_active=True,
                    valid_till__gte=date.today()
                ).exclude(id=offer_id).exists()

                if existing_offer:
                    messages.error(request, f'Another active offer already exists for this {offer.offer_type}')
                    return render(request, 'admin/offer_form.html', {
                        'form': form,
                        'offer_type': offer.offer_type,
                        'is_edit': True,
                        'offer': offer
                    })

                offer.save()
                messages.success(request, 'Offer updated successfully')
                return redirect('offer_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = OfferForm(
            instance=offer,
            offer_type=offer.offer_type
        )

    context = {
        'form': form,
        'offer_type': offer.offer_type,
        'is_edit': True,
        'offer': offer
    }
    return render(request, 'admin/offer_form.html', context)







def offer_list(request):
    today = date.today()
    
    product_offers = Offer.objects.filter(
        offer_type='product'
    ).select_related('product').order_by('-created_at')

    category_offers = Offer.objects.filter(
        offer_type='category'
    ).select_related('category').order_by('-created_at')

    context = {
        'product_offers': product_offers,
        'category_offers': category_offers,
        'current_date': today,
    }
    return render(request, 'admin/offer_list.html', context)

def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Offer deleted successfully')
        return redirect('offer_list')
    
    return redirect('offer_list')
###################################################################################################################################################
def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def create_coupon(request):
    if request.method == 'POST':
        form = CouponCreationForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f"Coupon '{coupon.coupon_code}' created successfully!")
            # return redirect('coupon_list')  
    else:
        form = CouponCreationForm()
    
    return render(request, 'admin/create_coupon.html', {
        'form': form,
        'title': 'Create New Coupon'
    })
    
def coupon_list(request):
    # Get all active, non-deleted coupons by default
    coupons = Coupon.objects.filter(is_deleted=False)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        coupons = coupons.filter(
            Q(coupon_name__icontains=search_query) | 
            Q(coupon_code__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        now = timezone.now()
        coupons = coupons.filter(
            is_active=True,
            valid_from__lte=now,
            valid_till__gte=now
        )
    elif status_filter == 'expired':
        now = timezone.now()
        coupons = coupons.filter(valid_till__lt=now)
    elif status_filter == 'upcoming':
        now = timezone.now()
        coupons = coupons.filter(valid_from__gt=now)
    elif status_filter == 'inactive':
        coupons = coupons.filter(is_active=False)
    
    # Filter by discount type
    discount_filter = request.GET.get('discount_type', '')
    if discount_filter in ['fixed', 'percent']:
        coupons = coupons.filter(discount_type=discount_filter)
    
    # Annotate coupons with usage count
    coupons = coupons.annotate(usage_count=Count('couponusage'))
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'created_at')
    sort_order = request.GET.get('order', 'desc')
    
    if sort_by in ['coupon_name', 'coupon_code', 'discount', 'min_purchase_amount', 'valid_till', 'created_at', 'usage_count']:
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        coupons = coupons.order_by(sort_by)
    
    # Context to pass to template
    context = {
        'coupons': coupons,
        'search_query': search_query,
        'status_filter': status_filter,
        'discount_filter': discount_filter,
        'sort_by': sort_by.replace('-', '') if sort_by.startswith('-') else sort_by,
        'sort_order': sort_order,
    }
    
    return render(request, 'admin/coupon_list.html', context)




def edit_coupon(request,coupon_id):
    coupon = get_object_or_404(Coupon,id=coupon_id,is_deleted=False)
    
    if request.method == 'POST':
        #populating the form with existing coupon data
        form = CouponCreationForm(request.POST,instance=coupon)
        if form.is_valid():
            updated_coupon = form.save()
            messages.success(request,f"Coupon updated successfully")
            return redirect('coupon_list')
        else:
            messages.error(request,"Please correct the error below")
    else:
        form=CouponCreationForm(instance=coupon)
    return render(request, 'admin/edit_coupon.html', {
        'form': form,
        'title': f'Edit Coupon: {coupon.coupon_code}',
        'coupon': coupon  
    })
    
def delete_coupon(request,coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)
    
    if request.method == 'POST':
        coupon.is_deleted  = True
        coupon.is_Active = False
        coupon.save()
        
        messages.success(request, f"Coupon '{coupon.coupon_code}' has been deleted successfully.")
        return redirect('coupon_list')
    
    return redirect('coupon_list')



#########################################################################################################################################################################################################
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, timedelta
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa

def sales_report(request):
    # Default to current month report with proper timezone handling
    today = timezone.now().date()
    start_date = timezone.make_aware(datetime.combine(today.replace(day=1), datetime.min.time()))
    end_date = timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))
    
    # Filter by date range
    report_type = request.GET.get('report_type', 'monthly')
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    order_status = request.GET.get('order_status', 'DELIVERED')  # Default to DELIVERED, but allow other statuses
    
    if report_type == 'daily':
        start_date = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    elif report_type == 'weekly':
        start_date = timezone.make_aware(datetime.combine(today - timedelta(days=7), datetime.min.time()))
    elif report_type == 'monthly':
        # Already set as default
        pass
    elif report_type == 'yearly':
        start_date = timezone.make_aware(datetime.combine(today.replace(month=1, day=1), datetime.min.time()))
    elif report_type == 'custom' and custom_start and custom_end:
        try:
            start_date = timezone.make_aware(datetime.strptime(custom_start, '%Y-%m-%d'))
            # Add 1 day to end_date and set time to 00:00:00 to include the entire end date
            end_date = timezone.make_aware(datetime.strptime(custom_end, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            # Handle invalid date formats
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
    
    # Create base query with date filter
    base_query = Order.objects.filter(
        ordered_date__gte=start_date,
        ordered_date__lt=end_date
    )
    
    # Apply order status filter but save a copy of the base query first
    # for other calculations that need different filters
    orders_query = base_query
    
    if order_status != 'ALL':
        orders_query = orders_query.filter(order_status=order_status)
    
    # Use the filtered orders for all calculations
    filtered_orders = orders_query
    
    # Basic sales metrics
    total_sales_count = filtered_orders.count()
    total_order_amount = filtered_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_discount = filtered_orders.aggregate(
        total_coupon_discount=Sum('coupon_discount'),
    )['total_coupon_discount'] or 0
    
    # Add product discounts from OrderItem
    order_items = OrderItem.objects.filter(order__in=filtered_orders)
    product_discount = order_items.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0
    total_discount += product_discount
    
    # Refunds and cancellations
    refunded_query = base_query.filter(payment_status='REFUNDED')
    if order_status != 'ALL':
        refunded_query = refunded_query.filter(order_status=order_status)
    total_refund_amount = refunded_query.aggregate(Sum('refund_amount'))['refund_amount__sum'] or 0
    
    canceled_query = base_query.filter(order_status='CANCELED')
    if order_status != 'ALL' and order_status != 'CANCELED':
        canceled_query = canceled_query.filter(order_status=order_status)
    total_canceled_count = canceled_query.count()
    
    # Adjust total revenue to account for refunds
    total_revenue = total_order_amount - total_discount - total_refund_amount
    
    # Payment method breakdown
    payment_methods = filtered_orders.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')
    
    # Top selling products
    top_products = OrderItem.objects.filter(
        order__in=filtered_orders
    ).values(
        'variant__product__name', 'variant__product__id'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_sales=Sum('total_amount')
    ).order_by('-quantity_sold')[:10]
    
    # Date formatting for display
    formatted_start_date = start_date.strftime('%Y-%m-%d')
    formatted_end_date = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    context = {
        'report_type': report_type,
        'order_status': order_status,
        'start_date': formatted_start_date,
        'end_date': formatted_end_date,
        'total_sales_count': total_sales_count,
        'total_order_amount': total_order_amount,
        'total_discount': total_discount,
        'total_revenue': total_revenue,
        'payment_methods': payment_methods,
        'top_products': top_products,
        'total_refund_amount': total_refund_amount,
        'total_canceled_count': total_canceled_count,
    }
    
    # Check if PDF download is requested
    if 'download_pdf' in request.GET:
        # Get the template
        template = get_template('admin/sales_report_pdf.html')
        
        # Render the template with context
        html = template.render(context)
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object, using the BytesIO buffer as its "file"
        pisa_status = pisa.CreatePDF(
            html,                   # the HTML to convert
            dest=buffer,           # the file buffer
            encoding='UTF-8'
        )
        
        # Close the PDF buffer
        buffer.seek(0)
        
        # Generate filename based on report type and date range
        filename = f"sales_report_{report_type}_{formatted_start_date}_to_{formatted_end_date}.pdf"
        
        # Create the HttpResponse object with appropriate PDF headers
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    # Regular HTML view render
    return render(request, 'admin/sales_report.html', context)


def is_Admin(user):
    return user.is_staff and user.is_superuser


@user_passes_test(is_Admin)
def admin_wallet_transactions(request):
    #getting the filter parameter
    """If the parameter exists, it returns the value.
       If the parameter does not exist, it returns '' (an empty string) instead of raising an error."""
    
    user_query = request.GET.get('user','')
    transaction_type = request.GET.get('type','')
    start_date = request.GET.get('start_date','')
    end_date = request.GET.get('end_date','')
    
    transactions = WalletTransaction.objects.all()
    
    #applying filters
    if user_query:
        transactions = transactions.filter(
            Q(wallet__user__username__icontains=user_query) |
            Q(wallet__user__email__icontains=user_query)
        )
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        transactions = transactions.filter(created_at__lte=end_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        transactions = transactions.filter(created_at__lte=end_date)
        
    #pagination
    paginator = Paginator(transactions, 20)  #20 transactions per page
    page_number = request.GET.get('page', 1)
    transactions_page = paginator.get_page(page_number)
    
    context = {
        'transactions': transactions_page,
        'user_query': user_query,
        'transaction_type': transaction_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'admin/wallet_transactions.html', context)



@user_passes_test(is_Admin)
def admin_user_wallet_details(request, user_id):
    user  = get_object_or_404(UserTable, id = user_id)
    wallet = user.wallet
    all_transactions = wallet.transactions.all().select_related('order')
    
    #calculating the summaries
    total_credits = sum(t.transaction_amount for t in all_transactions if t.transaction_type == 'credit')
    total_debits = sum(t.transaction_amount for t in all_transactions if t.transaction_type == 'debit')
    
    #order details
    order_transactions = all_transactions.filter(order__isnull=False)
    order_payments = order_transactions.filter(transaction_type='debit')
    order_refunds = order_transactions.filter(transaction_type='credit')
    
    #recently activity dates
    last_transaction = all_transactions.first()
    last_order_payment = order_payments.first()
    last_refund = order_refunds.first()
    
    #pagination
    paginator = Paginator(all_transactions, 20)  # 20 transactions per page
    page_number = request.GET.get('page', 1)
    transactions_page = paginator.get_page(page_number)
    
    context = {
        'user': user,
        'wallet': wallet,
        'transactions': transactions_page,
        'total_credits': total_credits,
        'total_debits': total_debits,
        'order_payments_count': order_payments.count(),
        'order_refunds_count': order_refunds.count(),
        'total_refunds': sum(t.transaction_amount for t in order_refunds),
        'last_transaction_date': last_transaction.created_at if last_transaction else None,
        'last_order_payment_date': last_order_payment.created_at if last_order_payment else None,
        'last_refund_date': last_refund.created_at if last_refund else None,
    }
    
    return render(request, 'admin/user_wallet_details.html', context)