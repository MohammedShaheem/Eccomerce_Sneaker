from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib import messages  # for setting passages if user logedin
from UserProfile.forms import UserRegForm
from UserProfile.models import UserTable
from django.contrib.auth.hashers import make_password,check_password #make password for encrypting and check password for decrypting
from AdminProfile.models import ProductTable
from .utils import generate_otp, verify_otp
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import random



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
    return render(request,'user/SPPage.html',{'product':product})
    """Tries to find a product in the database where id matches product_id,
        if found return the product object, if not found automatically 
        returns a 404 error page. This is safer than using product.object.get()
        which would raise an error if product isn't found"""
    
    

def home_before_login(request):
     # Redirect authenticated users to home
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'user/home_before_login.html')


   