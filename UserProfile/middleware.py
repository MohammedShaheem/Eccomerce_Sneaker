from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from AdminProfile.models import Cart

class NoCacheMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response



# class AuthenticationMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # List of URLs that don't require authentication
#         public_urls = ['/login/', '/signin/', '/', '/home_before_login/']
        
#         # Check if user is accessing protected URL without authentication
#         if not request.user.is_authenticated and request.path not in public_urls:
#             messages.warning(request, "Please login to access this page.")
#             return redirect('login')
            
#         response = self.get_response(request)
#         return response


