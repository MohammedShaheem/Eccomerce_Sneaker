from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib import messages  # for setting passages if user logedin
from UserProfile.forms import UserRegForm
from UserProfile.models import UserTable
from django.contrib.auth.hashers import make_password,check_password #make password for encrypting and check password for decrypting
from AdminProfile.models import ProductTable,Product,Category,ProductTable,VarianceTable,Color,Size,Product_Images_Table,Cart,CartItem
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
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.is_active = False
                user.save()

                email = form.cleaned_data['email']
                email_otp = generate_otp(email)
                print(f"email_otp:{email_otp}")
                
                # Store OTP in session with user_id as key
                request.session[f'otp_{user.id}'] = email_otp
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
                
                return redirect('verify_otp', user_id=user.id)
                
            except Exception as e:
                print(f"Error: {str(e)}")
                user.delete()
                messages.error(request, 'Email sending failed')
                
        messages.error(request, 'Please check your form')
    else:
        form = UserRegForm()
    
    return render(request, 'user/signin.html', {'form': form})

def verify_otp(request, user_id):
    try:
        user = UserTable.objects.get(id=user_id)
        
        if request.method == 'POST':
            submitted_otp = request.POST.get('email_otp')
            stored_otp = request.session.get(f'otp_{user_id}')
            print(f"submitted_otp:{submitted_otp}")
            print(f"stored_otp:{stored_otp}")
            
            if submitted_otp and stored_otp and submitted_otp == stored_otp:
                user.is_active = True
                user.is_email_verified = True
                user.save()
                
                # Clear OTP from session after successful verification
                request.session.pop(f'otp_{user_id}', None)
                
                messages.success(request, 'Email verified successfully!')
                return redirect('login')
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
        
        return render(request, 'user/otp-verification.html', {'user': user})
        
    except UserTable.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('signin')

#######################################################################################################################################################################################

def forgetpsswrd(request):
    return render(request,'user/forgot password.html')

#########################################################################################################################################################################################

def setnewtpsswrd(request):
    return render(request,'user/setnewpsswrd.html')

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
        'images',
        'variancetable_set__size',
        'variancetable_set__color'
    )
    return render(request,'user/menPage.html',{'products':products})


def single_product_page(request, product_id):
    product = get_object_or_404(ProductTable, id=product_id)#model name and the the id of the product to display whic comes from the url pattern.
    
    # get all variants for this product with thier stock informations
    variants = VarianceTable.objects.filter(
        product=product
    ).select_related(
        'size' # fetching size
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
                'is_available': variant.Stock_Quantity > 0
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
    print("hello")
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity',1))
        print(f"data:{data}")
        
        #validate inputs
        if not variant_id or quantity < 1:
            return JsonResponse({
                'success':False,
                'message':'Invalid input data'
            })
            
            # get variant
        try:
            variant = VarianceTable.objects.get(id=variant_id)
        except VarianceTable.DoesNotExist:
            return JsonResponse({
                'success':False,
                'message':'Product variant not found'
            })
            
        # check stock
        if variant.Stock_Quantity < quantity:
            return JsonResponse({
                'success':False,
                'message':f'Only {variant.Stock_Quantity} items available'
            })
            
        # get or create cart
        cart , _ = Cart.objects.get_or_create(user=request.user)
        
        # get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_variant=variant,
            defaults={'quantity':0}
        )
            
        # update quantity
        new_quantity = cart_item.quantity + quantity
        if new_quantity > variant.Stock_Quantity:
            return JsonResponse({
                'success': False,
                'message': f'Cannot add {quantity} more items. Stock limit reached.'
            })
        cart_item.quantity = new_quantity
        cart_item.save()
        cart.update_total()
            
            
        #return success response with updated cart info
        return JsonResponse({
                'success':False,
                'message':'Product added to cart sucessfully',
                'cart_count':cart.total_items,
                'cart_total':float(cart.grand_total)
            })
        
        
    except (ValueError, ValidationError) as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
    except Exception as e:
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
        'product_variant__product__images'
    ).all()
    
    print("Cart Items:", cart_items.count())
    
    subtotal = cart.grand_total
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
            
            # use float for JSON serialization
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