from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib import messages  # for setting passages if user logedin
from UserProfile.forms import UserRegForm,AddressForm,CancellationForm,ReturnForm
from UserProfile.models import UserTable,Address
from django.contrib.auth.hashers import make_password,check_password #make password for encrypting and check password for decrypting
from AdminProfile.models import ProductTable,Product,Category,VarianceTable,Color,Size,Product_Images_Table,Cart,CartItem,Order,OrderItem,Wishilist,Wallet,WalletTransaction,Offer,Coupon,CouponUsage,ReturnRequest,ReturnRequestItem,OrderAddress
from .utils import generate_otp, verify_otp,get_discounted_price
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import random
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import json
from decimal import Decimal
from django.db.models import Sum
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
import uuid
import re
from django.contrib.auth import update_session_auth_hash
import datetime
from django.urls import reverse
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.db.models import F, Q
import logging
from django.utils.timezone import now
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from decimal import Decimal



# Create your views here.


def login(request):
    if request.user.is_authenticated:
        if not request.user.is_staff and request.session.get('user_role') == 'user':
            return redirect('home')
        elif request.user.is_staff:
            messages.error(request, "Please log out from admin side first.")
            return redirect('admin_logout')  # Force logout from admin side

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = UserTable.objects.get(email=email)
            
            if user.is_staff:  # Block staff from user login
                messages.error(request, "Staff members must use the admin login.")
                return render(request, 'user/login.html')

            if not user.is_active:
                messages.error(request, "Your account is not active. Please verify your email.")
                return render(request, 'user/login.html')

            auth_user = authenticate(username=email, password=password)
            
            if auth_user is not None:
                auth_login(request, auth_user)
                request.session['user_role'] = 'user'  # Set role as user
                request.session['userMail'] = email
                messages.success(request, "Login successful!")
                return redirect('home')
            else:
                if not user.check_password(password):
                    messages.error(request, "Incorrect password")
                else:
                    messages.error(request, "Authentication failed. Please try again.")

        except UserTable.DoesNotExist:
            messages.error(request, "No account found with this email")
        except Exception as e:
            print(f"Unexpected error: {e}")
            messages.error(request, "An unexpected error occurred")

    return render(request, 'user/login.html')

#######################################################################################################################################################################################

def generate_otp(email):
    # Your OTP generation logic
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    return otp

def signin(request):
    if request.method == 'POST':
        form = UserRegForm(request.POST)
        if form.is_valid():
            try:
                # Storing form data in session
                user_data = {
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'password': form.cleaned_data['password'],
                    'Phone_number': form.cleaned_data['Phone_number']
                }
                request.session['user_registration_data'] = user_data
                email = form.cleaned_data['email']
                email_otp = generate_otp(email)
                print(f"email_otp:{email_otp}")
                # Storing OTP in session
                request.session['registration_otp'] = email_otp
                # Force save the session
                request.session.modified = True
                # Set session expiry for OTP (e.g., 10 minutes)
                request.session.set_expiry(600)

                subject = 'OTP Verification'
                message = 'Your verification OTP is: {}'.format(email_otp)
                
                send_mail(
                    subject,
                    message,
                    'mohammedshaheemtk2@gmail.com',  # From email
                    [email],  # To email
                    fail_silently=False,
                )
                
                return redirect('verify_otp')
                
            except Exception as e:
                print(f"Error: {str(e)}")
                messages.error(request, 'Email sending failed')
                
        messages.error(request, 'Please check your form')
    else:
        form = UserRegForm()
    
    return render(request, 'user/signin.html', {'form': form})

def verify_otp(request):
    
    print("OTP Verification View Called")
    print("Request Method:", request.method)
    print("All session keys:", list(request.session.keys()))
    print("Session data:", request.session.items())
    #checking the registration data in session
    user_data = request.session.get('user_registration_data')
    
    if not user_data:
        messages.error(request, 'Registration session expired')
        return redirect('signin')
    
    if request.method == 'POST':
        submitted_otp = request.POST.get('email_otp')
        stored_otp = request.session.get('registration_otp')
        print(f"submitted_otp:{submitted_otp}")
        print(f"stored_otp:{stored_otp}")
        
        if submitted_otp and stored_otp and submitted_otp == stored_otp:
            #create and save user only after OTP verification
            try:
                user = UserTable()
                user.username = user_data['username']
                user.email = user_data['email']
                user.set_password(user_data['password'])
                user.is_active = True
                user.is_email_verified = True
                user.save()
                
                #clear session data
                request.session.pop('user_registration_data', None)
                request.session.pop('registration_otp', None)
                
                messages.success(request, 'Registration successful! You can now log in.')
                return redirect('login')
            except Exception as e:
                print(f"Error creating user: {str(e)}")
                messages.error(request, 'Failed to create user account')
        else:
            messages.error(request, 'Invalid or expired OTP. Please try again.')
    
    return render(request, 'user/otp-verification.html')

#######################################################################################################################################################################################

def forgot_password(request):
    
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = UserTable.objects.get(email=email)
            
            #generating otp
            email_otp = generate_otp(email)
            print(f'otp:{email_otp}')
            
            #store otp in session
            request.session[f'pwd_otp_{user.id}'] = email_otp
            #set session expiy for otp(10minutes)
            request.session.set_expiry(600)
            
            #sent the otp via email
            subject = 'Password reset OTP'
            message = 'Your password reset OTP is: {}'.format(email_otp)
            
            send_mail(
                subject,
                message,
                'mohammedshaheemtk2@gmail.com',#from eamil
                [email],#to eamil
                fail_silently=False,
            )
            
            messages.success(request, 'OTP sent to your email')
            return redirect('verify_reset_otp',user_id=user.id)
        
        except UserTable.DoesNotExist:
            messages.error(request, 'Email not found')
        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, 'Failed to send OTP')
    
    
    
    
    return render(request,'user/forgot_password.html')

#############################################################################################################################################################################################3

def verify_reset_otp(request, user_id):
    try:
        user = UserTable.objects.get(id=user_id)
        
        if request.method == 'POST':
            submitted_otp = request.POST.get('email_otp')
            stored_otp = request.session.get(f'pwd_otp_{user_id}')
            
            print(f"Debug - submitted_otp: {submitted_otp}")
            print(f"Debug - stored_otp: {stored_otp}")
            
            if submitted_otp and stored_otp and submitted_otp == stored_otp:
                # Clear OTP from session after successful verification
                request.session.pop(f'pwd_otp_{user_id}', None)
                
                # Store that user is allowed to reset password
                request.session[f'can_reset_pwd_{user_id}'] = True
                request.session.modified = True  # Ensure session is saved
                request.session.set_expiry(300)  # 5 minutes to reset password
                
                print(f"Debug - Set can_reset_pwd_{user_id} to True")
                print(f"Debug - All session keys: {request.session.keys()}")
                
                messages.success(request, 'OTP verified successfully. Set your new password.')
                return redirect('reset_password', user_id=user_id)
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
        
        return render(request, 'user/reset_otp_verification.html', {'user': user})
        
    except UserTable.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('forgot_password')
    except Exception as e:
        print(f"Error in verify_reset_otp: {str(e)}")
        messages.error(request, 'An error occurred')
        return redirect('forgot_password')
    
#########################################################################################################################################################################################

def reset_password(request, user_id):
    print(f"Debug - Entered reset_password with user_id: {user_id}")
    print(f"Debug - Session keys: {request.session.keys()}")
    print(f"Debug - Can reset password: {request.session.get(f'can_reset_pwd_{user_id}')}")
    
    try:
        user = UserTable.objects.get(id=user_id)
        
        # Special case: Allow access if the request method is GET and coming from OTP verification
        referer = request.META.get('HTTP_REFERER', '')
        coming_from_otp = 'verify-reset-otp' in referer
        
        # Check if user is allowed to reset password
        if not request.session.get(f'can_reset_pwd_{user_id}') and not (request.method == 'GET' and coming_from_otp):
            print(f"Debug - Unauthorized access: can_reset_pwd_{user_id} not in session")
            messages.error(request, 'Unauthorized access. Please complete OTP verification first.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password and password == confirm_password:
                # Check if new password is the same as current password
                if user.check_password(password):
                    messages.error(request, 'New password cannot be the same as your current password.')
                    return render(request, 'user/reset_password.html', {'user': user})
                
                user.set_password(password)
                user.save()
                
                # Clear reset permission from session
                request.session.pop(f'can_reset_pwd_{user_id}', None)
                request.session.modified = True  # Ensure session is saved
                
                messages.success(request, 'Password reset successfully')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match')
        
        # If we got here, either it's GET and authorized, or it's POST with matching passwords
        return render(request, 'user/reset_password.html', {'user': user})
    
    except UserTable.DoesNotExist:
        print(f"Debug - User with id {user_id} not found")
        messages.error(request, 'Invalid user')
        return redirect('forgot_password')
    except Exception as e:
        print(f"Error in reset_password: {str(e)}")
        messages.error(request, 'An error occurred')
        return redirect('forgot_password')

#################################################################################################################################################################################
@login_required
def home(request):
    # Check both authentication and session
    if request.user.is_authenticated and request.session.get('userMail'):
        context = {
            'user': request.user,
            'email': request.session.get('userMail')
        }
        return render(request, 'user/home.html', context)
    
    # If session is missing but user is authenticated, restore session
    elif request.user.is_authenticated:
        request.session['userMail'] = request.user.email
        return redirect('home')
    
    messages.warning(request, "You must log in to access the home page.")
    return redirect('login')

################################################################################################################################################################################

def logout(request):
    # Clear both authentication and session
    if request.user.is_authenticated:
        auth_logout(request)
    
    if 'userMail' in request.session:
        request.session.flush()  # Clear all session data
    
    messages.success(request, "You have been logged out successfully.")
    return redirect('home_before_login')


#############################################################################################################################################################################
def Sneakers(request):
    products = ProductTable.objects.prefetch_related(
        'category',
        'variances__images',
        'variances__size',
        'variances__color'
    ).filter(category__category_name='sneakers',
        Is_deleted=False,Is_active=True)  
    
    # Get user's wishlist items
    user_wishlist_items = []
    if request.user.is_authenticated:
        user_wishlist_items = Wishilist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)
    
    # Get the sort parameter from the request
    sort_option = request.GET.get('sort', 'default')
    
    # Apply sorting based on user selection
    if sort_option == 'price_low_high':
        products = products.order_by('sale_Price')
    elif sort_option == 'price_high_low':
        products = products.order_by('-sale_Price')
    elif sort_option == 'new_arrival':
        products = products.order_by('-created_at')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    
    #calculate discounted proces for each product
    products_with_offers = []
    for product in products:
        discount_info = get_discounted_price(product)
        print(f"discount_info:{discount_info}")
        products_with_offers.append({
            'product':product,
            'discounted_info':discount_info
        })    
        print(f"products_with_offers:{products_with_offers}")
        
        
        
        
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(cart__user=request.user).count()
    else:
        cart = request.session.get('cart', {})
        cart_count = sum(item.get('quantity', 0) for item in cart.values())
    
    return render(request, 'user/Sneakers.html', {
        'products': products_with_offers,
        'current_sort': sort_option,
        'cart_count': cart_count,
        'user_wishlist_items': user_wishlist_items
    })
######################################################################################################################################################################################

def Boots(request):
    products = ProductTable.objects.prefetch_related(
        'category',
        'variances__images',
        'variances__size',
        'variances__color'
    ).filter(category__category_name='boots',
        Is_deleted=False,Is_active=True)  
    
    # Get user's wishlist items
    user_wishlist_items = []
    if request.user.is_authenticated:
        user_wishlist_items = Wishilist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)
    
    # Get the sort parameter from the request
    sort_option = request.GET.get('sort', 'default')
    
    # Apply sorting based on user selection
    if sort_option == 'price_low_high':
        products = products.order_by('sale_Price')
    elif sort_option == 'price_high_low':
        products = products.order_by('-sale_Price')
    elif sort_option == 'new_arrival':
        products = products.order_by('-created_at')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    
    #calculate discounted proces for each product
    products_with_offers = []
    for product in products:
        discount_info = get_discounted_price(product)
        print(f"discount_info:{discount_info}")
        products_with_offers.append({
            'product':product,
            'discounted_info':discount_info
        })    
        print(f"products_with_offers:{products_with_offers}")
        
        
        
        
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(cart__user=request.user).count()
    else:
        cart = request.session.get('cart', {})
        cart_count = sum(item.get('quantity', 0) for item in cart.values())
    
    return render(request, 'user/Boots.html', {
        'products': products_with_offers,
        'current_sort': sort_option,
        'cart_count': cart_count,
        'user_wishlist_items': user_wishlist_items
    })
#################################################################################################################################################################################
def Runners(request):
    products = ProductTable.objects.prefetch_related(
        'category',
        'variances__images',
        'variances__size',
        'variances__color'
    ).filter(category__category_name='Running',
        Is_deleted=False,Is_active=True)  
    
    # Get user's wishlist items
    user_wishlist_items = []
    if request.user.is_authenticated:
        user_wishlist_items = Wishilist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)
    
    # Get the sort parameter from the request
    sort_option = request.GET.get('sort', 'default')
    
    # Apply sorting based on user selection
    if sort_option == 'price_low_high':
        products = products.order_by('sale_Price')
    elif sort_option == 'price_high_low':
        products = products.order_by('-sale_Price')
    elif sort_option == 'new_arrival':
        products = products.order_by('-created_at')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    
    #calculate discounted proces for each product
    products_with_offers = []
    for product in products:
        discount_info = get_discounted_price(product)
        print(f"discount_info:{discount_info}")
        products_with_offers.append({
            'product':product,
            'discounted_info':discount_info
        })    
        print(f"products_with_offers:{products_with_offers}")
        
        
        
        
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(cart__user=request.user).count()
    else:
        cart = request.session.get('cart', {})
        cart_count = sum(item.get('quantity', 0) for item in cart.values())
    
    return render(request, 'user/Boots.html', {
        'products': products_with_offers,
        'current_sort': sort_option,
        'cart_count': cart_count,
        'user_wishlist_items': user_wishlist_items
    })
############################################################################################################################################################################################3
def single_product_page(request, product_id):
    product = get_object_or_404(ProductTable, id=product_id)#model name and the the id of the product to display whic comes from the url pattern.
    
    #getting all variants for this product with thier stock informations
    variants = VarianceTable.objects.filter(
        product=product
    ).select_related(
        'size',
    ).prefetch_related(
        'images'
    ).order_by(
        'size__size' # order by size value
    )
    
    #getting the related product of the same category,excluding he same product
    related_products = ProductTable.objects.filter(
        category = product.category,
        Is_deleted=False
    ).exclude(
        id=product.id
    ).prefetch_related(
        'variances',
        'variances__images'
    )[:4]#limiting 4 related products
    
    #checking if product is completely out of stock
    is_out_of_stock = not variants.filter(Stock_Quantity__gt=0).exists()
    
    #calculatting the discounted proce for the product
    discount_info = get_discounted_price(product)
    
    #adding discounted price info to related products as well
    related_products_with_offers = [
        {
            'product': related_product,
            'discounted_info': get_discounted_price(related_product)
        }
        for related_product in related_products
    ]
    user_wishlist_items = []
    if request.user.is_authenticated:
        user_wishlist_items = Wishilist.objects.filter(user=request.user).values_list('product_id', flat=True)
        
    wishlist_count = Wishilist.objects.filter(user=request.user).count()
    
    
     # Get cart count
    cart = Cart.objects.get(user=request.user, is_active=True)
    cart_count = cart.total_items
        
        
    context = {
        'product': product,
        'variants': variants,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'user_wishlist_items': user_wishlist_items,
        'is_out_of_stock': is_out_of_stock,
        'related_products': related_products_with_offers,  
        'available_sizes': [
            {
                'id': variant.id,
                'size': variant.size.size,
                'stock': variant.Stock_Quantity,
                'is_available': variant.Stock_Quantity > 0,
                'images': [image.image.url for image in variant.images.all()]
            }
            for variant in variants
        ],
        'discounted_info': discount_info  # Add discount info to context
    }
    
    return render(request, 'user/SPPage.html', context)
################################################################################################################################################################################

def home_before_login(request):
     # Redirect authenticated users to home
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'user/home_before_login.html')


################################################################################################################################################################################
logger = logging.getLogger(__name__)

def clean_cart_of_deleted_products(cart):
    """
    remove deleted/blocked products from cart
    returns number of items removed
    """
    deleted_items = cart.items.filter(
        Q(product_variant__product__Is_deleted=True) |
        Q(product_variant__product__Is_active=False) |
        Q(product_variant__product__product_quantity=0)
    )
    
    removed_count = deleted_items.count()
    deleted_items.delete()
    if removed_count > 0:
        cart.update_total()
    return removed_count


@require_POST
@login_required
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
        
        if not variant_id or quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Invalid input data'
            })
            
        try:
            variant = VarianceTable.objects.select_related('product').get(
                id=variant_id,
                product__Is_deleted=False,
                product__Is_active=True
            )
            discount_info = get_discounted_price(variant.product)
            product_price = discount_info['final_price']
            print(f"product_price from discount: {product_price}")
        except VarianceTable.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product is no longer available'
            })
            
        if variant.Stock_Quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {variant.Stock_Quantity} items available'
            })
            
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        try:
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_variant=variant,
                defaults={
                    'quantity': quantity,
                    'item_price': product_price,
                    'total_price': product_price * quantity
                }
            )
            
            if not created:
                new_quantity = cart_item.quantity + quantity
                if new_quantity > variant.Stock_Quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'Cannot add {quantity} more items. Stock limit reached.'
                    })
                cart_item.quantity = new_quantity
                cart_item.total_price = product_price * new_quantity  # Explicitly set total_price
                cart_item.save()
            
            cart.update_total()
            print(f"cart.grand_total after update: {cart.grand_total}")
            
            cart_count = CartItem.objects.filter(cart__user=request.user).count()
            
            return JsonResponse({
                'success': True,
                'message': 'Item added to cart successfully',
                'cart_count': cart.total_items,
                'cart_total': float(cart.grand_total)
            })
            
            
            
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
            
    except Exception as e:
        print(f"Error in add_to_cart: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while adding to cart'
        })
#######################################################################################################################################################################################################################
@login_required
def cart(request):
    try:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'grand_total': 0.00}
        )
        
        removed_count = clean_cart_of_deleted_products(cart)
        if removed_count > 0:
            messages.warning(
                request,
                f'{removed_count} items were removed from your cart as they are no longer available'
            )
        
        
        cart_items = cart.items.select_related(
            'product_variant',
            'product_variant__product',
            'product_variant__size',
            'product_variant__color'
        ).prefetch_related(
            'product_variant__images'
        ).all()
        
        for item in cart_items:
            if item.quantity > item.product_variant.Stock_Quantity:
                messages.warning(request, f"Quantity for {item.product_variant.product.name} exceeds available stock")

        
        #recalculate totals
        subtotal = Decimal('0.00')
        original_total = Decimal('0.00')
        for item in cart_items:
            discount_info = get_discounted_price(item.product_variant.product)
            print(f"item.total_price:{item.total_price}")
            subtotal += item.total_price
            
            original_total += discount_info['original_price'] * item.quantity
            print(f"Item: {item.product_variant.product.name}, item_price={item.item_price}, total_price={item.total_price}, original_price={discount_info['original_price']}")
        
        #update cart grand_total if it differs
        if cart.grand_total != subtotal:
            cart.grand_total = subtotal
            cart.save()
            print(f"Updated cart.grand_total to: {cart.grand_total}")
        
        discount = original_total - subtotal
        # tax_rate = Decimal('0')
        # tax_amount = subtotal * tax_rate
        total = subtotal 
        
        print(f"subtotal: {subtotal}")
        print(f"original_total: {original_total}")
        print(f"discount: {discount}")
        # print(f"tax_amount: {tax_amount}")
        print(f"total: {total}")
        
        context = {
            "cart_items": cart_items,
            'cart': cart,
            "cart_total": cart.grand_total,
            "subtotal": subtotal,
            "original_total": original_total,
            "discount": discount,
            # "tax_amount": tax_amount,
            "total": total,
            "item_count": cart.total_items,
        }
        
        return render(request, 'user/cart.html', context)
    
    except Exception as e:
        print(f"Error in cart view: {str(e)}")
        return render(request, 'user/cart.html', {'error': str(e)})
#######################################################################################################################################################################################
@login_required
def get_cart_count(request):
    try:
        cart = Cart.objects.get(user=request.user, is_active=True)
        cart_count = CartItem.objects.filter(cart=cart).count()
    except Cart.DoesNotExist:
        cart_count = 0
    
    return JsonResponse({'cart_count': cart_count})
#############################################################################################################################################################################
@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            
            # Validateing quantity against stock
            if quantity > cart_item.product_variant.Stock_Quantity:
                return JsonResponse({
                    'success': False,
                    'message': 'Requested quantity exceeds available stock'
                })
            
            if quantity < 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Quantity cannot be less than 1'
                })
            
            cart_item.quantity = quantity
            cart_item.save()
            cart = cart_item.cart
            cart.update_total()
            
            
            return JsonResponse({
                'success': True,
                'message': 'Quantity updated successfully',
                'new_total': float(cart.grand_total),
                'item_count': int(cart.total_items),
                'item_total': float(cart_item.total_price)
            })
           
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })
#################################################################################################################################################################################
    
@login_required
def remove_from_cart(request, item_id):
    
    try:
        cart_item = get_object_or_404(CartItem,
                                      id=item_id,
                                      cart__user=request.user)
        
        cart = cart_item.cart
        cart_item.delete()
        cart.update_total()
        
        return JsonResponse({
            "success":True,
            "message":'Item removed form cart',
            'new total':cart.grand_total,
            "item_count":cart.total_items,
            
            
        })

    except Exception as e:
        return JsonResponse({
            'success':False,
            'message':'Error removing item from cart'
            
        })
################################################################################################################################################################################        
import logging

logger = logging.getLogger(__name__)
@login_required
def clear_cart(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
            cart.update_total()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart cleared successfully',
                'new_total': cart.grand_total,
                'item_count': cart.total_items
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error clearing cart'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        })
        
##############################################################################################################################################################################################        
        
def add_address(request):
    # Determine source (where the user is coming from)
    source = request.GET.get('source', 'checkout')  # Default to checkout if not specified
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            #checking for default address logic before saving
            if address.is_default:
                #setting all other addresses to non-default
                Address.objects.filter(user=request.user).update(is_default=False)
            elif not Address.objects.filter(user=request.user, is_default=True).exists():
                #if no default exists, set this as default
                address.is_default = True
                
            address.save()
            
            messages.success(request, 'Address saved successfully.')
            # Redirect based on the hidden field value
            redirect_source = request.POST.get('redirect_source', 'checkout')
            if redirect_source == 'profile':
                return redirect('user_address')  # Redirect to user's address book
            else:
                return redirect('checkout')  # Redirect to checkout 
            
    else:
        form = AddressForm()
    
    return render(request, 'user/add_address.html', {'form': form, 'source': source})
#####################################################################################################################################################################################################
@login_required
def apply_coupon(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    coupon_code = request.POST.get('coupon_code', '').strip().upper()
    if not coupon_code:
        return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})
    
    try:
        coupon = Coupon.objects.get(coupon_code=coupon_code, is_active=True, is_deleted=False)
        cart = Cart.objects.get(user=request.user)
        cart_total = cart.items.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        discount, error = coupon.apply(request.user, cart_total)
        if discount is not None:
            request.session['applied_coupon_code'] = coupon_code
            return JsonResponse({
                'success': True,
                'message': f"Coupon '{coupon_code}' applied successfully!",
                'discount': float(discount),
                'coupon_name': coupon.coupon_name,
                'total_amount': float(cart_total + Decimal('0') - discount)  # Adjust delivery_charge as needed
            })
        else:
            if 'applied_coupon_code' in request.session:
                del request.session['applied_coupon_code']
            return JsonResponse({'success': False, 'message': error})
    except Coupon.DoesNotExist:
        if 'applied_coupon_code' in request.session:
            del request.session['applied_coupon_code']
        return JsonResponse({'success': False, 'message': 'Invalid coupon code'})
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Your cart is empty'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Server error occurred'}, status=500)

@login_required
@require_POST
def remove_coupon(request):
    try:
        # Remove the coupon from session
        if 'applied_coupon_code' in request.session:
            del request.session['applied_coupon_code']
        
        # Get the cart total without discount
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.filter(
            product_variant__product__Is_deleted=False,
            product_variant__product__Is_active=True
        )
        cart_total = cart_items.aggregate(total=Sum('total_price'))['total'] or Decimal('0')

        return JsonResponse({
            'success': True,
            'message': 'Coupon removed successfully',
            'total_amount': float(cart_total)  # Return the updated total
        })
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Your cart is empty'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Server error occurred'
        }, status=500)

@login_required
def checkout(request):
    cart = None
    cart_items = []
    coupon_error = None
    applied_coupon = None
    coupon_discount = Decimal('0')
    coupons = Coupon.objects.all()
    try:
        cart = Cart.objects.get(user=request.user)
        
        removed_count = clean_cart_of_deleted_products(cart)
        if removed_count > 0:
            messages.warning(
                request,
                f'{removed_count} items were removed from your cart as they are no longer available'
            )
            return redirect('cart')
        
        cart_items = CartItem.objects.filter(
            cart=cart,
            product_variant__product__Is_deleted=False,
            product_variant__product__Is_active=True    
        )
        for item in cart_items:
            if item.quantity > item.product_variant.Stock_Quantity:
                messages.warning(request, f"Cannot proceed to checkout! {item.product_variant.product.name} exceeds available stock.")
                return redirect('cart')  
                
        if not cart_items.exists():
            messages.error(request, "Your cart is empty")
            return redirect('cart')
        
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    user_addresses = Address.objects.filter(user=request.user)
    
    # Calculate cart total
    cart_total = cart_items.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    delivery_charge = Decimal('0')
    
    #handleing POST actions
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'remove_coupon':
            if 'applied_coupon_code' in request.session:
                del request.session['applied_coupon_code']
                messages.success(request, "Coupon removed successfully!")
                
    #validating applied coupon 
    applied_coupon_code = request.session.get('applied_coupon_code')
    if applied_coupon_code:
        try:
            coupon = Coupon.objects.get(coupon_code=applied_coupon_code)
            discount, error = coupon.apply(request.user, cart_total)
            if discount is not None:
                applied_coupon = coupon
                coupon_discount = discount
            else:
                coupon_error = error
                del request.session['applied_coupon_code']
        except Coupon.DoesNotExist:
            coupon_error = "Invalid coupon code"
            del request.session['applied_coupon_code']
    
    total_amount = cart_total + delivery_charge - coupon_discount
    wallet = request.user.wallet
    has_sufficient_balance = wallet.has_sufficient_balance(total_amount)
    
    context = {
        'user_addresses': user_addresses,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'delivery_charge': delivery_charge,
        'coupon_discount': coupon_discount,
        'total_amount': total_amount,
        'address_form': AddressForm(),
        'wallet_balance': wallet.balance,
        'has_sufficient_balance': has_sufficient_balance,
        'applied_coupon': applied_coupon,
        'coupon_error': coupon_error,
        'coupons':coupons
    }
    
    return render(request, 'user/checkout.html', context)


            

@login_required
def create_order(request):
    if request.method == 'POST':
        try:
            # Validate cart
            cart = Cart.objects.select_related('user').prefetch_related(
                'items',
                'items__product_variant',
                'items__product_variant__product'
            ).get(user=request.user, is_active=True)
            
            
            
            removed_count = clean_cart_of_deleted_products(cart)
            if removed_count > 0:
                messages.warning(
                    request,
                    f'{removed_count} items were removed as they are no longer available'
                )
                return redirect('checkout')
            
            if not cart.items.exists():
                messages.error(request, "Your cart is empty")
                return redirect('checkout')
            
            cart_total = cart.items.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
            delivery_charge = Decimal('0')  
            total_amount = cart_total + delivery_charge

            # Validate address
            address_id = request.POST.get('address')
            if not address_id:
                messages.error(request, "Please select a delivery address")
                return redirect('checkout')
            address = Address.objects.get(id=address_id, user=request.user)

            # Validate payment method
            payment_method = request.POST.get('payment_method')
            if payment_method not in ['COD', 'WALLET', 'UPI']:
                messages.error(request, "Invalid payment method")
                return redirect('checkout')
            if payment_method == 'COD' and total_amount > Decimal('1000'):
                messages.error(request, "Cash on Delivery is not available for orders above ₹1000. Please choose another payment method.")
                return redirect('checkout')
            has_offer_applied = False
            
            # Calculate total first
            total_amount = Decimal('0')
            for item in cart.items.all():
                if item.product_variant.Stock_Quantity < item.quantity:
                    raise ValueError(f"Sorry, {item.product_variant} is out of stock")
                total_amount += item.item_price * item.quantity
                
                discount_info = get_discounted_price(item.product_variant.product)
                item_offer = discount_info['offer']
                
                if item_offer:
                    has_offer_applied = True

            if total_amount <= 0:
                messages.error(request, "Invalid order amount")
                return redirect('checkout')
                
            #getting the applied coupon code if any is applied
            applied_coupon_code = request.session.get('applied_coupon_code')
            coupon = None
            coupon_discount = Decimal('0')
        
            if applied_coupon_code:
                try:
                    coupon = Coupon.objects.get(coupon_code=applied_coupon_code, is_active=True, is_deleted=False)
                    
                    #checking if user has already used this coupon
                    if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
                        messages.error(request, f"You have already used the coupon '{coupon.coupon_code}'.")
                        del request.session['applied_coupon_code']#deleting the session
                        return redirect('checkout')
                    
                    #checking if coupon is still valid and usable
                    if not coupon.is_valid() or not coupon.can_use():
                        messages.error(request, f"The coupon '{coupon.coupon_code}' is no longer valid or has reached its usage limit.")
                        del request.session['applied_coupon_code']
                        return redirect('checkout')
                    
                    
                    #checking minimum purchase amount
                    if cart_total < coupon.min_purchase_amount:
                        messages.error(request, f"This coupon requires a minimum purchase of ₹{coupon.min_purchase_amount}.")
                        del request.session['applied_coupon_code']
                        return redirect('checkout')
                    
                    if coupon.discount_type == 'fixed':
                        coupon_discount = min(coupon.discount,cart_total)
                    else: #percentage
                        coupon_discount = min((cart_total * coupon_discount / 100),cart_total)
                    
                    
                                        
                    # Update the total amount with the discount
                    total_amount -= coupon_discount
                    
                except Coupon.DoesNotExist:
                    messages.error(request, "Applied coupon is no longer valid.")
                    return redirect('checkout')
            
            
            
            

            # Generate order ID
            order_id = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            if payment_method == 'WALLET':
                # Check wallet balance
                wallet = request.user.wallet
                if not wallet.has_sufficient_balance(total_amount):
                    messages.error(request, "Insufficient wallet balance")
                    return redirect('checkout')
                
                try:
                    with transaction.atomic():
                        # Process wallet payment
                        wallet.debit(total_amount, f"Payment for order #{order_id}")
                        
                        # Create the order with paid status
                        order = create_order_instance(
                            order_id=order_id,
                            user=request.user,
                            address=address,
                            payment_method=payment_method,
                            total_amount=total_amount,
                            cart=cart,
                            payment_status='PAID',
                            offer_applied=has_offer_applied
                        )
                        
                        # Mark coupon as used only after successful order creation
                        if coupon:
                            order.coupon = coupon
                            order.coupon_discount = coupon_discount
                            order.save()
                            CouponUsage.objects.create(
                                user=request.user,
                                coupon=coupon
                            )
                            del request.session['applied_coupon_code']
                    
                    messages.success(request, f"Order placed successfully! Order ID: {order_id}")
                    return redirect('order_confirmation', order_id=order_id)
                
                except Exception as e:
                    # If anything fails, transaction will be rolled back (including coupon usage)
                    messages.error(request, f"Error processing wallet payment: {str(e)}")
                    return redirect('checkout')
            
            elif payment_method == 'UPI':
                
                
                logger.info("Processing UPI payment")
                logger.info(f"Preparing session data for cart with {cart.items.count()} items")
                for item in cart.items.all():
                    logger.info(f"Cart Item - Product ID: {item.product_variant.product.id}, Variant ID: {item.product_variant.id}, Quantity: {item.quantity}, Price: {item.item_price}")
                
                # Store necessary data in session instead of creating order
                request.session['pending_order'] = {
                    'address_id': address_id,
                    'total_amount': str(total_amount),  # Convert Decimal to string for session
                    'cart_items': [
                        {
                            'variant_id': item.product_variant.id,
                            'quantity': item.quantity,
                            'price': str(item.item_price)
                        } for item in cart.items.all()
                    ],
                    'coupon_id': coupon.id if coupon else None,
                    'coupon_discount': str(coupon_discount) if coupon_discount > 0 else '0'
                }
                logger.info(f"Session data stored: {request.session['pending_order']}")

                # Create PayPal payment
                paypal_dict = {
                    'business': settings.PAYPAL_RECEIVER_EMAIL,
                    'amount': str(f"{total_amount:.2f}"),
                    'item_name': f'Order for {request.user.username}',
                    'invoice': f"TEMP-{uuid.uuid4().hex[:6].upper()}",
                    'currency_code': 'USD',
                    'notify_url': request.build_absolute_uri(reverse('paypal-ipn')),
                    'return_url': request.build_absolute_uri(reverse('payment_success')),
                    'cancel_return': request.build_absolute_uri(reverse('payment_cancelled')),
                }
                print(f"paypal_dict: {paypal_dict}")
                logger.info(f"PayPal payment initiated with: {paypal_dict}")

                form = PayPalPaymentsForm(initial=paypal_dict)
                return render(request, 'user/process_payment.html', {
                    'form': form,
                    'total_amount': total_amount
                })
            
            else:  # Handle COD
                # Create order
                order = create_order_instance(
                            order_id=order_id,
                            user=request.user,
                            address=address,
                            payment_method=payment_method,
                            total_amount=total_amount,
                            cart=cart,
                            payment_status='PENDING',  #COD is pending until delivery
                            offer_applied=has_offer_applied
                        )
                
                #marking coupon as used only after successful order creation
                if coupon:
                    order.coupon = coupon
                    order.coupon_discount = coupon_discount
                    order.save()
                    CouponUsage.objects.create(
                        user=request.user,
                        coupon=coupon
                    )
                    del request.session['applied_coupon_code']

                messages.success(request, f"Order placed successfully! Order ID: {order_id}")
                return redirect('order_confirmation', order_id=order_id)

        except Exception as e:
            messages.error(request, str(e))
            return redirect('checkout')

    return redirect('checkout')

def create_order_instance(order_id, user, address, payment_method, total_amount, cart, payment_status, offer_applied=False):
    """Helper function to create order and order items"""
    with transaction.atomic():
        # Debug cart contents
        print("Cart contents:")
        for cart_item in cart.items.all():
            variant = cart_item.product_variant
            product = variant.product
            print(f"Cart Item - Product ID: {product.id}, Variant ID: {variant.id}, Quantity: {cart_item.quantity}")

        removed_count = clean_cart_of_deleted_products(cart)
        if removed_count > 0:
            raise ValueError("Some items in your cart are no longer available")
        
        if not cart.items.exists():
            raise ValueError('Your cart is empty')
        
        # Create order
        order = Order.objects.create(
            order_id=order_id,
            user=user,
            payment_method=payment_method,
            total_amount=total_amount,
            order_status='PENDING',
            payment_status=payment_status,
            offer_applied=offer_applied
        )
        #create the order address 
        OrderAddress.objects.create(
            order=order,
            full_name=address.name,  
            phone=address.phone,
            email=address.email,
            address_type = address.address_type,
            house_name=address.house_name,
            city=address.city,
            state=address.state,
            pincode=address.pincode
        )

        # Create order items and update stock
        order_items = []
        for cart_item in cart.items.all():
            variant = cart_item.product_variant
            product = variant.product  # Get product from variant

            # Update stock for variant
            if variant.Stock_Quantity < cart_item.quantity:
                raise ValueError(f"Insufficient stock for {product.name}")
            variant.Stock_Quantity -= cart_item.quantity
            variant.save()

            # Update total product quantity
            product.product_quantity = product.variances.aggregate(
                total=Sum('Stock_Quantity')
            )['total'] or 0
            product.save()

            # Get offer info
            discount_info = get_discounted_price(product)
            item_offer = discount_info['offer']

            # Create OrderItem
            order_items.append(OrderItem(
                order=order,
                variant=variant,
                product=product,
                quantity=cart_item.quantity,
                price_per_item=cart_item.item_price,
                total_amount=cart_item.quantity * cart_item.item_price,
                item_status='PENDING',
                item_payment_status=payment_status,
                offer=item_offer
            ))
        
        if not order_items:
            raise ValueError("No valid items to create order from")

        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()
        
        return order

@csrf_exempt
def payment_success(request):
    pending_order = request.session.get('pending_order')
    if not pending_order:
        logger.error("No pending order found in session")
        messages.error(request, "No pending order found")
        return redirect('home')

    try:
        logger.info("Processing payment success for UPI")
        logger.info(f"Pending order data from session: {pending_order}")
        
        address = Address.objects.get(id=pending_order['address_id'], user=request.user)
        
        has_offer_applied = False
        for item in pending_order['cart_items']:
            variant = VarianceTable.objects.get(id=item['variant_id'])
            product = variant.product
            logger.info(f"Processing Item - Variant ID: {variant.id}, Product ID: {product.id}, Quantity: {item['quantity']}, Price: {item['price']}")
            discount_info = get_discounted_price(product)
            if discount_info['offer']:
                has_offer_applied = True

        order_id = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        order = Order.objects.create(
            order_id=order_id,
            user=request.user,
            payment_method='UPI',
            total_amount=Decimal(pending_order['total_amount']),
            order_status='PENDING',
            payment_status='PAID',
            offer_applied=has_offer_applied
        )
        OrderAddress.objects.create(
            order=order,
            full_name=address.name,  
            phone=address.phone,
            email=address.email,
            address_type = address.address_type,
            house_name=address.house_name,
            city=address.city,
            state=address.state,
            pincode=address.pincode
        )

        order_items = []
        for item in pending_order['cart_items']:
            variant = VarianceTable.objects.get(id=item['variant_id'])
            product = variant.product
            quantity = item['quantity']
            
            logger.info(f"Creating OrderItem - Order: {order_id}, Product ID: {product.id}, Variant ID: {variant.id}, Quantity: {quantity}")
            
            if variant.Stock_Quantity < quantity:
                order.delete()
                raise ValueError(f"Sorry, {variant} is out of stock")
                
            variant.Stock_Quantity -= quantity
            variant.save()
            
            product.product_quantity -= quantity
            product.save()
            
            discount_info = get_discounted_price(product)
            item_offer = discount_info['offer']
            
            order_items.append(OrderItem(
                order=order,
                variant=variant,
                product=product,
                quantity=quantity,
                price_per_item=Decimal(item['price']),
                total_amount=Decimal(item['price']) * quantity,
                item_status='PENDING',
                item_payment_status='PAID',
                offer=item_offer
            ))
        
        OrderItem.objects.bulk_create(order_items)
        
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        
        del request.session['pending_order']
        
        logger.info(f"Order {order_id} created successfully with {len(order_items)} items")
        for item in order.items.all():
            logger.info(f"Created OrderItem - Product ID: {item.product.id}, Variant ID: {item.variant.id}")
        
        messages.success(request, "Payment completed successfully!")
        return redirect('order_confirmation', order_id=order_id)
        
    except Exception as e:
        logger.error(f"Payment success failed: {str(e)}", exc_info=True)
        messages.error(request, str(e))
        return redirect('checkout')

@csrf_exempt
def payment_cancelled(request):
    if 'pending_order' in request.session:
        del request.session['pending_order']
    messages.warning(request, "Payment was cancelled")
    return redirect('checkout')




#configuring Instant Payment Notification IPN
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver

import logging

logger = logging.getLogger(__name__)

@receiver(valid_ipn_received)
def payment_notification(sender, **kwargs):
    ipn_obj = sender
    logger.info(f"PayPal IPN received: {ipn_obj.payment_status}")
    if ipn_obj.payment_status == 'Completed':
        try:
            order = Order.objects.get(order_id=ipn_obj.invoice)
            order.payment_status = 'PAID'
            order.save()
            logger.info(f"Order {ipn_obj.invoice} payment updated to PAID")
        except Order.DoesNotExist:
            logger.warning(f"No order found for invoice {ipn_obj.invoice}")

@login_required
def order_confirmation(request, order_id):
    try:
        order = Order.objects.prefetch_related('items__product').get(
            order_id=order_id,
            user=request.user
        )
        
        context = {
            'order': order,
            'items': order.items.all(),
            'address': order.order_address,
        }
        
        return render(request, 'user/order_confirmation.html', context)
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('home')
##############################################################################################################################################################################################
@login_required
def generate_invoice(request,order_id):
    try:
        #fetching the order with all related items and product informations
        order = Order.objects.prefetch_related(
            'items__variant__product'
        ).select_related(
            'user','order_address'
        ).get(
            order_id=order_id,
            user=request.user
        )
        
        #checking if the payment is completed
        if order.payment_status != 'PAID':
            messages.warning(request,"Invoice is only availabe for paid orders")
            return redirect('order_detail',order_id=order_id)
        
        #calculating the subtotal
        subtotal = order.total_amount
        if hasattr(order,'coupon_discount') and order.coupon_discount:
            subtotal = order.coupon_discount
            
        context = {
            'order': order,
            'items': order.items.all(),
            'address': order.order_address,
            'subtotal': subtotal,
            'company_name': 'Your Company Name',
            'company_address': 'Your Company Address',
            'company_phone': 'Your Company Phone',
            'company_email': 'your@email.com',
            
        }
        
        #get the template
        template = get_template('user/invoice_template.html')
        
        #rendering the template with context
        html  = template.render(context)
        
        #creating a file like buffer to receive pdf data
        buffer = BytesIO()
        
        #create the pdf object using the bytesio buffer as its file
        pisa_status = pisa.CreatePDF(
            html,
            dest=buffer,
            encoding='UTF-8'
        )
        
        #closing the pdf buffer
        buffer.seek(0)
        
        #generate filename
        filename = f"Invoice_{order_id}.pdf"
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('home')
##############################################################################################################################################################################################################


@login_required
def user_profile(request):
    return render(request,'user/user_profile.html',{'user':request.user})
##################################################################################################################################################################################################

@login_required
def user_address(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request,'user/user_address.html',{'addresses':addresses})
##################################################################################################################################################################################

@login_required
def update_address(request, address_id):
    address = get_object_or_404(Address, id=address_id,user=request.user)
    
    if request.method == 'POST':
        address.name = request.POST.get('name')
        address.house_name = request.POST.get('house_name')
        address.street = request.POST.get('street')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.pincode = request.POST.get('pincode')
        address.email = request.POST.get('email')
        address.phone = request.POST.get('phone')
        address.address_type = request.POST.get('address_type')
        address.landmark = request.POST.get('landmark')
        
        try:
            address.save()
            messages.success(request,'Address updated successfully')
            return redirect('user_address')
        except Exception as e:
            messages.error(request,f"Error updating address: {str(e)}")
            
    return render(request, 'user/update_user_address.html', {'address': address})
################################################################################################################################################################################################

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address,id=address_id)
    
    
    try:
        #if this is the default address and there other address make other address default
        if address.is_default:
            other_address = Address.objects.filter(
                user=request.user
            ).exclude(id=address_id).first()
            
            if other_address:
                other_address.is_default = True
                other_address.save()
        
        #deleting
        address.delete()
        messages.success(request, 'Address deleted successfully')
        
        return redirect('user_address')
    
    except Exception as e:
        messages.error(request,f"Error deleting address:{str(e)}")

        return redirect('user_address')

########################################################################################################################################################################

@login_required
def user_profile_edit(request):
    user = request.user
    
    if request.method == 'POST':
        
        #getting the form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        
        
        #username validation
        if not username or len(username) < 3 or len(username) > 30:
            messages.error(request, "Username must be between 3 and 30 characters")
            return render(request, 'user/user_profile_edit.html', {'user': user})
        
        if not re.match(r'^[a-zA-Z]+$', username):
            messages.error(request, 'Username can only contain letters.')
            return render(request, 'user/user_profile_edit.html', {'user': user})
        
        #check if username is already taken by another user
        if UserTable.objects.exclude(id=user.id).filter(username=username).exists():
            messages.error(request, 'This username is already taken.')
            return render(request, 'user/user_profile_edit.html', {'user': user})
        
        # Email validation
        if not email:
            messages.error(request, 'Email is required.')
            return render(request, 'user/user_profile_edit.html', {'user': user})
            
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'user/user_profile_edit.html', {'user': user})
            
        # Check if email is already taken by another user
        if UserTable.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return render(request, 'user/user_profile_edit.html', {'user': user})
        
        #validate phone number
        if not re.match(r'^[6-9]\d{9}$', phone_number):
            messages.error(request, 'Enter a valid 10-digit phone number starting with 6, 7, 8, or 9.')
            return render(request, 'user/user_profile_edit.html', {'user': user})
        
        #update the profile info
        user.username = username
        user.email = email
        user.phone_number = phone_number
        
        
        #password change
        if current_password and new_password and confirm_password:
            #verify current password
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'user/user_profile_edit.html', {'user': user})
                
            #validate new password
            if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', new_password):
                messages.error(request, 'Password must be at least 8 characters long and include a letter and a number.')
                return render(request, 'user/user_profile_edit.html', {'user': user})
            
            #confirm password match
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return render(request, 'user/user_profile_edit.html', {'user': user})
            
            #set new password
            user.set_password(new_password)
            password_changed = True
        else:
            password_changed = False
        try:
            user.save()
            messages.success(request, 'Profile updated successfully')
            
            # If password was changed, re-authenticate the user
            if password_changed:
                update_session_auth_hash(request, user)  # Keep user logged in
                
            return redirect('user_profile')  
            
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")
    
    
    return render(request, 'user/user_profile_edit.html', {'user': user})
            
#########################################################################################################################
@login_required
@require_POST
def set_default_address(request, address_id):
    
    if Address.set_default(address_id, request.user):
        messages.success(request, 'Default address updated successfully.')
    else:
        messages.error(request, 'Unable to update default address.')
    
    
    return redirect('user_address')  
##################################################################################################################################################################################



@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    return render(request, 'user/order_list.html', {'orders': orders})

    
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    items = order.items.all()
    if order.return_status == 'REQUESTED':
        messages.warning(request, 'Your return request is being reviewed by our team.')
    elif order.return_status == 'APPROVED':
        messages.success(request, 'Your return request has been approved.')
        if order.refund_amount:
            messages.success(request, f'Refund amount: ₹{order.refund_amount}')
            if order.refund_date:
                messages.success(request, f'Refunded on {order.refund_date.strftime("%B %d, %Y")}')
    elif order.return_status == 'REJECTED':
        messages.error(request, 'Your return request has been rejected.')
        if order.return_requests.last() and order.return_requests.last().admin_notes:
            messages.error(request, f'Reason: {order.return_requests.last().admin_notes}')

    return render(request, 'user/order_detail.html', {
        'order': order,
        'items':items
    })
    
logger = logging.getLogger(__name__)  # Add logging for debugging

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Check if order can be canceled
    if order.order_status in ['DELIVERED', 'CANCELED', 'RETURNED']:
        messages.error(request, 'This order cannot be canceled.')
        return redirect('order_detail', order_id=order_id)
    
    if request.method == 'GET':
        form = CancellationForm()
    else:
        form = CancellationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order.order_status = 'CANCELED'
                    order.canceled_date = datetime.datetime.now()
                    order.cancellation_reason = form.cleaned_data['reason']
                    
                    # Restock quantities
                    for item in order.items.all():
                        product = item.product
                        variant = item.variant
                        quantity = item.quantity
                        if product:
                            product.product_quantity += quantity
                            product.save()
                        if variant:
                            variant.Stock_Quantity += quantity
                            variant.save()
                    
                    # Handle refund based on payment method
                    if order.payment_status == 'PAID':
                        order.payment_status = 'REFUNDED'
                        order.refund_amount = order.total_amount
                        order.refund_date = datetime.datetime.now()
                        
                        if order.payment_method in ['UPI', 'WALLET']:
                            logger.info(f"Refunding {order.total_amount} to wallet for order {order.order_id}")
                            request.user.wallet.credit(
                                amount=order.total_amount,
                                description=f"Refund for canceled order #{order.order_id}",
                                order=order,
                                transaction_category='ORDER_CANCELLATION'
                            )
                            messages.success(request, f'₹{order.total_amount} has been credited to your wallet')
                        else:
                            logger.info(f"No wallet refund for {order.payment_method} payment method")
                    
                    order.save()
                    messages.success(request, 'Your order has been canceled successfully.')
                
                return redirect('order_list')
                
            except Exception as e:
                logger.error(f"Error in cancel_order: {str(e)}")
                messages.error(request, f'Error processing cancellation: {str(e)}')
                return redirect('order_detail', order_id=order_id)
    
    return render(request, 'user/cancel_order.html', {
        'order': order,
        'form': form
    })
    
@login_required
def cancel_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    # Check if item can be canceled
    if order.order_status in ['DELIVERED', 'CANCELED', 'RETURNED'] or item.is_canceled or item.is_returned:
        messages.error(request, 'This item cannot be canceled.')
        return redirect('order_detail', order_id=order_id)
    
    if request.method == 'GET':
        form = CancellationForm()
    else:
        form = CancellationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update item status
                    item.is_canceled = True
                    item.cancelation_reason = form.cleaned_data['reason']
                    item.item_status = 'CANCELED'
                    
                    # Restore stock quantities
                    if item.product:
                        item.product.product_quantity += item.quantity
                        item.product.save()
                    if item.variant:
                        item.variant.Stock_Quantity += item.quantity
                        item.variant.save()
                    
                    item.save()
                    
                    # Recalculate order total and status
                    active_items = order.items.filter(is_canceled=False, is_returned=False)
                    if active_items.count() == 0:
                        order.order_status = 'CANCELED'
                        order.canceled_date = datetime.datetime.now()
                        order.cancellation_reason = "All items canceled"
                        if order.payment_status == 'PAID':
                            order.payment_status = 'REFUNDED'
                    else:
                        order.total_amount = sum(item.total_amount for item in active_items)
                    
                    # Handle refund for the specific item
                    if order.payment_status in ['PAID', 'REFUNDED']:
                        refund_amount = item.total_amount
                        order.refund_amount = (order.refund_amount or Decimal('0.00')) + refund_amount
                        order.refund_date = datetime.datetime.now()
                        
                        if order.payment_method in ['UPI', 'WALLET']:
                            logger.info(f"Refunding {refund_amount} to wallet for item {item.id} in order {order.order_id}")
                            request.user.wallet.credit(
                                amount=refund_amount,
                                description=f"Refund for canceled item from order #{order.order_id}",
                                order=order,
                                transaction_category='ORDER_CANCELLATION'
                            )
                            messages.success(request, f'₹{refund_amount} has been credited to your wallet')
                        else:
                            logger.info(f"No wallet refund for {order.payment_method} payment method")
                    
                    order.save()
                    messages.success(request, 'The item has been canceled successfully.')
                
                return redirect('order_detail', order_id=order_id)
                
            except Exception as e:
                logger.error(f"Error in cancel_order_item: {str(e)}")
                messages.error(request, f'Error processing cancellation: {str(e)}')
                return redirect('order_detail', order_id=order_id)
    
    return render(request, 'user/cancel_order_item.html', {
        'order': order,
        'item': item,
        'form': form
    })
######################################################################################################################################################################################################

@login_required
@require_POST
def toggle_wishlist(request, product_id):
    try:
        product = get_object_or_404(ProductTable, id=product_id)
        wishlist_item = Wishilist.objects.filter(
            user=request.user,
            product=product
        ).first()
        
        if wishlist_item:
            # If item exists, remove it
            wishlist_item.delete()
            return JsonResponse({'status': 'removed'})
        else:
            # If item doesn't exist, add it
            Wishilist.objects.create(user=request.user, product=product)
            return JsonResponse({'status': 'added'})
            
    except Exception as e:
        print(f"Error in toggle_wishlist: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@login_required
def wishlist_view(request):
    # getting wishlist items with all related data in a single query
    wishlist_items = Wishilist.objects.filter(user=request.user)\
        .select_related('product')\
        .prefetch_related(
            'product__variances',           
            'product__variances__images'    
        )
    
    #for each wishlist item getting all the available variants and discount adding price
    for item in wishlist_items:
        item.discount_data = get_discounted_price(item.product)
        item.available_variants = VarianceTable.objects.filter(
            product=item.product,
            Stock_Quantity__gt=0
        ).select_related('size', 'color')
    
    context = {
        'wishlist_items': wishlist_items
    }
    
    return render(request, 'user/wishlist.html', context)
    
logger = logging.getLogger(__name__)

@login_required
@require_POST
def add_to_cart_from_wishlist(request):
    try:
        # Log the incoming request data for debugging
        logger.info(f"add_to_cart_from_wishlist request data: {request.POST}")
        
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        remove_from_wishlist = request.POST.get('remove_from_wishlist', 'false').lower() == 'true'
        
        if not variant_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Please select a variant'
            }, status=400)
            
        # Get variant with additional checks
        variant = get_object_or_404(VarianceTable, id=variant_id, product__Is_deleted=False, product__Is_active=True)
        logger.info(f"Found variant: {variant}")
        
        # Get or create user's cart
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        logger.info(f"Cart for user {request.user.username}, created: {created}")
        
        # Add item to cart using the model's method
        try:
            cart_item = cart.add_item(variant)
            logger.info(f"Added item to cart: {cart_item}")
        except Exception as e:
            logger.error(f"Error adding item to cart: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to add item to cart: {str(e)}'
            }, status=400)
        
        if remove_from_wishlist:
            Wishilist.objects.filter(
                user=request.user,
                product_id=product_id
            ).delete()
            logger.info(f"Removed product {product_id} from wishlist for user {request.user.username}")
        
        # Return success response with cart count and total (optional for frontend update)
        return JsonResponse({
            'status': 'success',
            'message': 'Item added to cart successfully',
            'cart_count': cart.total_items,  # Assuming Cart has a total_items property
            'cart_total': float(cart.grand_total) if cart.grand_total else 0.0
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in add_to_cart_from_wishlist: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)

@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    try:
        wishlist_item = Wishilist.objects.get(user=request.user, product_id=product_id)
        wishlist_item.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed from wishlist'
        })
    except Wishilist.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Item not found in wishlist'
        }, status=404)
###############################################################################################################################################################################################################        
        
@login_required
def wallet_dashboard(request):
    wallet = request.user.wallet
    transactions = wallet.transactions.all()[:10]  # Get last 10 transactions
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    return render(request, 'user/wallet_dashboard.html', context)

@login_required
@require_POST
def process_wallet_payment(request):
    try:
        amount = Decimal(request.POST.get('amount', 0))
        order_id = request.POST.get('order_id')
        
        wallet = request.user.wallet
        
        if not wallet.has_sufficient_balance(amount):
            return JsonResponse({
                'success': False,
                'message': 'Insufficient wallet balance'
            })
        
        # Process the payment
        wallet.debit(amount, f"Payment for order #{order_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully',
            'new_balance': str(wallet.balance)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def process_refund_to_wallet(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        refund_amount = order.total_amount
        
        # Credit the refund amount to wallet
        request.user.wallet.credit(
            refund_amount,
            f"Refund for order #{order_id}",
            order=order
        )
        
        # Update order status
        order.status = 'refunded'
        order.payment_status = 'refunded'
        order.save()
        
        messages.success(request, f'Refund of {refund_amount} has been credited to your wallet')
        return redirect('wallet_dashboard')
    except Exception as e:
        messages.error(request, f'Error processing refund: {str(e)}')
        return redirect('order_detail', order_id=order_id)
    

@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Check if the order can be returned (only delivered orders)
    if order.order_status != 'DELIVERED':
        messages.error(request, 'Only delivered orders can be returned')
        return redirect('order_detail', order_id=order_id)
    
    # Check if a return request is already being processed
    if order.return_status in ['REQUESTED', 'APPROVED']:
        messages.info(request, 'A return request for this order is already being processed')
        return redirect('order_detail', order_id=order_id)
    
    # Filter returnable items (not canceled and not already returned)
    returnable_items = order.items.filter(
        is_canceled=False,
        item_return_status='NONE'
    )
    
    if request.method == 'GET':
        form = ReturnForm()
        return render(request, 'user/return_order.html', {
            'order': order,
            'form': form,
            'returnable_items': returnable_items
        })
        
    form = ReturnForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                # Get selected items for return
                selected_items = request.POST.getlist('return_items')
                if not selected_items:
                    messages.error(request, 'Please select at least one item to return')
                    return redirect('return_order', order_id=order_id)
                
                # Create a return request
                return_request = ReturnRequest.objects.create(
                    order=order,
                    user=request.user,
                    reason=form.cleaned_data['reason'],
                    status='REQUESTED'
                )
                
                # Add items to return request
                for item_id in selected_items:
                    item = get_object_or_404(OrderItem, id=item_id, order=order)
                    
                    # Skip if item is canceled or already returned
                    if item.is_canceled or item.item_return_status != 'NONE':
                        continue
                    
                    # Create return record
                    ReturnRequestItem.objects.create(
                        return_request=return_request,
                        order_item=item
                    )
                    
                    # Update item return status
                    item.item_return_status = 'REQUESTED'
                    item.return_reason = form.cleaned_data['reason']
                    item.save()
                
                # Update order return status only if at least one item is being returned
                if return_request.items.exists():
                    order.return_status = 'REQUESTED'
                    order.save()
                else:
                    return_request.delete()
                    messages.error(request, 'No valid items selected for return')
                    return redirect('return_order', order_id=order_id)
                
                messages.success(request, 'Return request submitted successfully. Your request is under review.')
                return redirect('order_detail', order_id=order_id)
                
        except Exception as e:
            messages.error(request, f'Error processing return request: {str(e)}')
            return redirect('order_detail', order_id=order_id)
    
    return render(request, 'user/return_order.html', {
        'order': order,
        'form': form,
        'returnable_items': returnable_items
    })
#########################################################################################################################################################################################################
    
