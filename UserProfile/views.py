from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib import messages  # for setting passages if user logedin
from UserProfile.forms import UserRegForm,AddressForm,CancellationForm,ReturnForm
from UserProfile.models import UserTable,Address
from django.contrib.auth.hashers import make_password,check_password #make password for encrypting and check password for decrypting
from AdminProfile.models import ProductTable,Product,Category,ProductTable,VarianceTable,Color,Size,Product_Images_Table,Cart,CartItem,Order,OrderItem,Wishilist,Wallet,WalletTransaction,ReturnedItem
from .utils import generate_otp, verify_otp
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



# Create your views here.


def login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Find the user by email
            user = UserTable.objects.get(email=email)
            
            # Detailed debugging
            print(f"User found: {user}")
            print(f"User is active: {user.is_active}")
            print(f"User password is valid: {user.has_usable_password()}")

            # Check if user is active
            if not user.is_active:
                messages.error(request, "Your account is not active. Please verify your email.")
                return render(request, 'user/login.html')

            # Authenticate using the user's credentials
            auth_user = authenticate(username=email, password=password)
            print(f"auth_user: {auth_user}")
            
            print(f"Authentication result: {auth_user}")

            if auth_user is not None:
                auth_login(request, auth_user)
                request.session['userMail'] = email
                messages.success(request, "Login successful!")
                return redirect('home')
            else:
                # If authentication fails, check password
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
                #storing form data in session 
                user_data = {
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'password': form.cleaned_data['password'],
                    'Phone_number':form.cleaned_data['Phone_number']
                }
                
                request.session['user_registration_data'] = user_data
                
                email = form.cleaned_data['email']
                email_otp = generate_otp(email)
                print(f"email_otp:{email_otp}")
                
                #storing OTP in session
                request.session['registration_otp'] = email_otp
                #set session expiry for OTP (e.g., 10 minutes)
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
def MenPage(request):
    products = ProductTable.objects.prefetch_related(
        'category',
        'variances__images',
        'variances__size',
        'variances__color'
    ).filter(Is_deleted=False)  
    
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
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(cart__user=request.user).count()
    else:
        cart = request.session.get('cart', {})
        cart_count = sum(item.get('quantity', 0) for item in cart.values())
    
    return render(request, 'user/menPage.html', {
        'products': products,
        'current_sort': sort_option,
        'cart_count': cart_count,
        'user_wishlist_items': user_wishlist_items
    })
######################################################################################################################################################################################

def single_product_page(request, product_id):
    product = get_object_or_404(ProductTable, id=product_id)#model name and the the id of the product to display whic comes from the url pattern.
    
    # get all variants for this product with thier stock informations
    variants = VarianceTable.objects.filter(
        product=product
    ).select_related(
        'size',
    ).prefetch_related(
        'images'
    ).order_by(
        'size__size' # order by size value
    )
    
    # check if product is completely out of stock
    is_out_of_stock = not variants.filter(Stock_Quantity__gt=0).exists()
    
    context = {
        'product': product,
        'variants': variants,
        'is_out_of_stock': is_out_of_stock,
        'available_sizes': [
            {
                'id': variant.id,
                'size': variant.size.size,
                'stock': variant.Stock_Quantity,
                'is_available': variant.Stock_Quantity > 0,
                'images': [image.image.url for image in variant.images.all()]
            }
            for variant in variants
        ]
    }
    
    return render(request, 'user/SPPage.html', context)
################################################################################################################################################################################

def home_before_login(request):
     # Redirect authenticated users to home
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'user/home_before_login.html')


################################################################################################################################################################################
@require_POST
@login_required
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
        
        # Validate inputs
        if not variant_id or quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Invalid input data'
            })
            
        # Get variant
        try:
            variant = VarianceTable.objects.select_related('product').get(id=variant_id)
            product_price = variant.product.sale_Price  # Get the price from product
        except VarianceTable.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product variant not found'
            })
            
        # Check stock
        if variant.Stock_Quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {variant.Stock_Quantity} items available'
            })
            
        # Get or create cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        try:
            # Get or create cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_variant=variant,
                defaults={
                    'quantity': quantity,
                    'item_price': product_price,  # Use product's sale price
                    'total_price': product_price * quantity  # Calculate initial total price
                }
            )
            
            if not created:
                # Update quantity if item already exists
                new_quantity = cart_item.quantity + quantity
                if new_quantity > variant.Stock_Quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'Cannot add {quantity} more items. Stock limit reached.'
                    })
                cart_item.quantity = new_quantity
                cart_item.save()  # This will trigger the save method which updates total_price
            
            cart.update_total()
            
            # Return success response with updated cart info
            return JsonResponse({
                'success': True,
                'message': 'Product added to cart successfully',
                'cart_count': cart.total_items,
                'cart_total': float(cart.grand_total)
            })
            
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
            
    except Exception as e:
        print(f"Error in add_to_cart: {str(e)}")  # For debugging
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while adding to cart'
        })
#######################################################################################################################################################################################################################
@login_required
def cart(request):
    cart,created = Cart.objects.get_or_create(
        user=request.user,
        defaults={'grand_total':0.00}
    )
    print(f"user:{request.user}")
    print(f"cart:{cart}")
    
    
    cart_items = cart.items.select_related(
        'product_variant',
        'product_variant__product',
        'product_variant__size',
        'product_variant__color'
        
    ).prefetch_related(
        'product_variant__images'
    ).all()
    
    print("Cart Items:", cart_items.count())
    
    subtotal = Decimal(cart.grand_total)
    tax_rate = Decimal(0.10)
    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount
    
    context = {
        "cart_items":cart_items,
        'cart':cart,
        "cart_total":cart.grand_total,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total": total,
        "item_count" : cart.total_items,
    }
    
    
    return render(request,'user/cart.html',context)
#######################################################################################################################################################################################

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
            return redirect('checkout') 
            
    else:
        form = AddressForm()
    
    return render(request, 'user/add_address.html', {'form': form})
#####################################################################################################################################################################################################
@login_required
def checkout(request):
    # Existing code remains the same until context
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
    except Cart.DoesNotExist:
        cart_items = []
        cart = None

    user_addresses = Address.objects.filter(user=request.user)
    
    cart_total = 0
    if cart_items:
        cart_total = cart_items.aggregate(
            total=Sum('total_price')
        )['total'] or 0
    
    delivery_charge = 0  
    coupon_discount = 0
    
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
        'wallet_balance':wallet.balance,
        'has_sufficient_balance': has_sufficient_balance
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


            # Calculate total
            total_amount = Decimal('0')
            for item in cart.items.all():
                if item.product_variant.Stock_Quantity < item.quantity:
                    raise ValueError(f"Sorry, {item.product_variant} is out of stock")
                total_amount += item.product_variant.product.sale_Price * item.quantity


            if total_amount <= 0:
                messages.error(request, "Invalid order amount")
                return redirect('checkout')

            # Generate order ID
            order_id = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            if payment_method == 'WALLET':
                #check wallet balance
                wallet = request.user.wallet
                if not wallet.has_sufficient_balance(total_amount):
                    messages.error(request, "Insufficient wallet balance")
                    return redirect('checkout')
                
                try:
                    with transaction.atomic():
                        #processing wallet payment
                        wallet.debit(total_amount,f"Payment for order #{order_id}")
                        
                        #creating the order with paid status
                        order = create_order_instance(
                            order_id=order_id,
                            user=request.user,
                            address=address,
                            payment_method=payment_method,
                            total_amount=total_amount,
                            cart=cart,
                            payment_status='PAID'
                        )
                    
                    messages.success(request, f"Order placed successfully! Order ID: {order_id}")
                    return redirect('order_confirmation', order_id=order_id)
                
                except Exception as e:
                    # If anything fails, transaction will be rolled back
                    messages.error(request, f"Error processing wallet payment: {str(e)}")
                    return redirect('checkout')
            
            elif payment_method == 'UPI':
                # Store necessary data in session instead of creating order
                request.session['pending_order'] = {
                    'address_id': address_id,
                    'total_amount': str(total_amount),  # Convert Decimal to string for session
                    'cart_items': [
                        {
                            'variant_id': item.product_variant.id,
                            'quantity': item.quantity,
                            'price': str(item.product_variant.product.sale_Price)
                        } for item in cart.items.all()
                    ]
                }

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
                print(f"paypal_dict:{paypal_dict}")
                logger.info(f"PayPal payment initiated with: {paypal_dict}")

                form = PayPalPaymentsForm(initial=paypal_dict)
                return render(request, 'user/process_payment.html', {
                    'form': form,
                    'total_amount': total_amount
                })
            
            else:  #handle COD 
                # Create order
                order = Order.objects.create(
                    order_id=order_id,
                    user=request.user,
                    shipping_address=address,
                    payment_method=payment_method,
                    total_amount=total_amount,
                    order_status='PENDING',
                    payment_status='PENDING' if payment_method == 'COD' else 'PAID'
                )


                messages.success(request, f"Order placed successfully! Order ID: {order_id}")
                return redirect('order_confirmation', order_id=order_id)

        except Exception as e:
            messages.error(request, str(e))
            return redirect('checkout')

    return redirect('checkout')

def create_order_instance(order_id, user, address, payment_method, total_amount, cart, payment_status):
    """helper function to create order and order items"""
    with transaction.atomic():
        # Create order
        order = Order.objects.create(
            order_id=order_id,
            user=user,
            shipping_address=address,
            payment_method=payment_method,
            total_amount=total_amount,
            order_status='PENDING',
            payment_status=payment_status
        )

        # Create order items and update stock
        order_items = []
        for cart_item in cart.items.all():
            cart_item.product_variant.Stock_Quantity -= cart_item.quantity
            cart_item.product_variant.save()
            
            product = cart_item.product_variant.product
            product.product_quantity = product.variances.aggregate(
                total=Sum('Stock_Quantity')
            )['total'] or 0
            product.save()
            
            order_items.append(OrderItem(
                order=order,
                variant=cart_item.product_variant,
                quantity=cart_item.quantity,
                price_per_item=cart_item.product_variant.product.sale_Price,
                total_amount=cart_item.quantity * cart_item.product_variant.product.sale_Price
            ))
        
        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()
        
        return order

@csrf_exempt
def payment_success(request):
    pending_order = request.session.get('pending_order')
    if not pending_order:
        messages.error(request, "No pending order found")
        return redirect('home')

    try:
        # Get address
        address = Address.objects.get(
            id=pending_order['address_id'],
            user=request.user
        )

        # Create order
        order_id = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        order = Order.objects.create(
            order_id=order_id,
            user=request.user,
            shipping_address=address,
            payment_method='UPI',
            total_amount=Decimal(pending_order['total_amount']),
            order_status='PENDING',
            payment_status='PAID'
        )

        # Create order items
        order_items = []
        for item in pending_order['cart_items']:
            variant = VarianceTable.objects.get(id=item['variant_id'])
            quantity = item['quantity']
            
            if variant.Stock_Quantity < quantity:
                order.delete()
                raise ValueError(f"Sorry, {variant} is out of stock")
                
            variant.Stock_Quantity -= quantity
            variant.save()
            
            order_items.append(OrderItem(
                order=order,
                variant=variant,
                quantity=quantity,
                price_per_item=Decimal(item['price']),
                total_amount=Decimal(item['price']) * quantity
            ))
        
        OrderItem.objects.bulk_create(order_items)
        
        # Clear cart
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        
        # Clear session
        del request.session['pending_order']
        
        messages.success(request, "Payment completed successfully!")
        return redirect('order_confirmation', order_id=order_id)
        
    except Exception as e:
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
            'address': order.shipping_address,
        }
        
        return render(request, 'user/order_confirmation.html', context)
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('home')
##############################################################################################################################################################################################
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
    return render(request, 'user/order_detail.html', {
        'order': order,
        'items': items
    })
    
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
                    
                    #handleing refund based on payment method
                    if order.payment_status == 'PAID':
                        order.payment_status = 'REFUNDED'
                        order.refund_amount = order.total_amount
                        order.refund_date = datetime.datetime.now()
                        
                        #if payment was made via UPI refund to wallet
                        if order.payment_method == 'UPI':
                            request.user.wallet.credit(
                                amount=order.total_amount,
                                description=f"Refund for canceled order #{order.order_id}"
                            )
                            messages.success(request, f'₹{order.total_amount} has been credited to your wallet')
                    
                    order.save()
                    messages.success(request, 'Your order has been canceled successfully.')
                    
                return redirect('order_list')
                
            except Exception as e:
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
    
    if order.order_status in ['DELIVERED', 'CANCELED', 'RETURNED'] or item.is_returned:
        messages.error(request, 'This item cannot be canceled.')
        return redirect('order_detail', order_id=order_id)
    
    if request.method == 'GET':
        form = CancellationForm()
    else:
        form = CancellationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    item.is_returned = True
                    item.return_date = datetime.datetime.now()
                    item.return_reason = form.cleaned_data['reason']
                    item.save()
                    
                    #recalculateing order total
                    remaining_items = order.items.filter(is_returned=False)
                    if remaining_items.count() == 0:
                        order.order_status = 'CANCELED'
                        order.canceled_date = datetime.datetime.now()
                        order.cancellation_reason = "All items canceled"
                    else:
                        new_total = sum(item.total_amount for item in remaining_items)
                        order.total_amount = new_total
                    
                    #handleing refund for the specific item
                    if order.payment_status == 'PAID':
                        refund_amount = item.total_amount
                        order.refund_amount = (order.refund_amount or 0) + refund_amount
                        order.refund_date = datetime.datetime.now()
                        
                        #if payment was made via UPI refund to wallet
                        if order.payment_method == 'UPI':
                            request.user.wallet.credit(
                                amount=refund_amount,
                                description=f"Refund for canceled item from order #{order.order_id}"
                            )
                            messages.success(request, f'₹{refund_amount} has been credited to your wallet')
                    
                    order.save()
                    messages.success(request, 'The item has been canceled successfully.')
                    
                return redirect('order_detail', order_id=order_id)
                
            except Exception as e:
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
    # Get wishlist items with all related data in a single query
    wishlist_items = Wishilist.objects.filter(user=request.user)\
        .select_related('product')\
        .prefetch_related(
            'product__variances',           # Use the correct related_name
            'product__variances__images'    # Chain to fetch images
        )
    
    # For each wishlist item get all the available variants
    for item in wishlist_items:
        item.available_variants = VarianceTable.objects.filter(
            product=item.product,
            Stock_Quantity__gt=0
        ).select_related('size', 'color')
    
    context = {
        'wishlist_items': wishlist_items
    }
    
    return render(request, 'user/wishlist.html', context)
    
@login_required
@require_POST
def add_to_cart_from_wishlist(request):
    try:
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        remove_from_wishlist = request.POST.get('remove_from_wishlist') == 'true'
        
        if not variant_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Please select a variant'
            }, status=400)
            
        variant = get_object_or_404(VarianceTable, id=variant_id)
        
        #get or create user's cart
        cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
        
        # adding the item to cart using the model's method
        cart.add_item(variant)
        
        if remove_from_wishlist:
            Wishilist.objects.filter(
                user=request.user,
                product_id=product_id
            ).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Item added to cart successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

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
            f"Refund for order #{order_id}"
        )
        
        # Update order status
        order.status = 'refunded'
        order.save()
        
        messages.success(request, f'Refund of {refund_amount} has been credited to your wallet')
        return redirect('wallet_dashboard')
    except Exception as e:
        messages.error(request, f'Error processing refund: {str(e)}')
        return redirect('order_detail', order_id=order_id)
    

@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    #checking if the order can be returned only delivered oreders
    if order.order_status != 'DELIVERED':
        messages.error(request, 'Only delivered orders can be returned')
        return redirect ('order_detail', order_id=order_id)
    
    
    #check if return period has expired 
    # return_window = timezone.now() - timezone.timedelta(days=7)
    # if order.delivered_date and order.delivered_date < return_window:
    #     messages.error(request, 'Return period has expired')
    #     return redirect('order_details', order_id=order_id)
    
    if request.method == 'GET':
        form = ReturnForm()
        return render(request, 'user/return_order.html',{
            'order':order,
            'form':form
        })
        
    form = ReturnForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                #creating return entries for selected items
                selected_items = request.POST.getlist('return_items')
                if not selected_items:
                    messages.error(request, 'Please select at least one item to return')
                    return redirect('return_order',order_id=order_id)
                
                total_refund = 0
                for item_id in selected_items:
                    item = get_object_or_404(OrderItem, id=item_id, order=order)
                    
                    #checking if the item is already returned
                    if hasattr(item, 'returneditem'):
                        continue
                    
                    #creating return record
                    ReturnedItem.objects.create(
                        order_item = item,
                        return_reason=form.cleaned_data['reason']
                    )
                    
                    total_refund += item.total_amount
                
                #updating order status if all items are returned
                all_items_returned = all(
                    hasattr(item, 'returneditem') 
                    for item in order.items.all()
                )
                if all_items_returned:
                    order.order_status = 'RETURNED'
                    
                #processing refund to wallet
                if total_refund > 0:
                    request.user.wallet.credit(
                        amount=total_refund,
                        description=f"Refund for returned items from order #{order.order_id}"
                    )
                    messages.success(
                        request, 
                        f'₹{total_refund} has been credited to your wallet'
                    )
                
                order.save()
                messages.success(request, 'Return request submitted successfully.')
                return redirect('order_detail', order_id=order_id)
                
        except Exception as e:
            messages.error(request, f'Error processing return: {str(e)}')
            return redirect('order_detail', order_id=order_id)
    
    return render(request, 'user/return_order.html', {
        'order': order,
        'form': form
    })
                    