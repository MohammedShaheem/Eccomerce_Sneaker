from django.http import HttpResponseForbidden
from django.urls import resolve

class RestrictAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        #initializes the middleware with request processing function

    def __call__(self, request):
        #processes the request and then returns the response
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        #view_func: the view function that will be exicuted
        
        
        
        admin_prefix = '/admin_profile/'  #routes for admin-related pages
        user_prefix = '/user_profile/'    #routes for user-related pages
        current_path = request.path        #get the current request path

        if request.user.is_authenticated:#checking if user is logged in
            #retriving user role from the session(set during login)
            
            user_role = request.session.get('user_role',None)
            
            
            if request.user.is_staff:
                if user_role != 'admin': #user should be an admin,but session role is not admin
                    #preventing acess to the admin side if logged in as a user
                    if current_path.startswith(admin_prefix):
                        return HttpResponseForbidden("Log in as an admin to access this area.")
                    return None
            
                #if logged in as an admin but trying to access user pages
                if current_path.startswith(user_prefix):
                        return HttpResponseForbidden("Staff members cannot access the user side.")
                
            else:
                #if an regular user
                if user_role != 'user':
                    if current_path.startswith(user_prefix):
                        return HttpResponseForbidden("Log in as a user to access this area.")
                return None

                #if logged in as a user but trying to access admin pages
                if current_path.startswith(admin_prefix):
                    return HttpResponseForbidden("Regular users cannot access the admin side.")

        return None  