from django.urls import path
from . import views
urlpatterns = [
    path('',views.home_before_login,name='home_before_login'),
    path('login/',views.login,name='login'),
    path('forgotpassword/',views.forgetpsswrd,name='forgetpsswrd'),
    path('setnewtpsswrd/',views.setnewtpsswrd,name='setnewtpsswrd'),
    path('home/',views.home,name='home'),
    path('logout/',views.logout,name='logout'),
    path('menpage/',views.MenPage,name='MenPage'),
    path('products/<int:product_id>/single_product_page/', views.single_product_page, name='single_product_page'),
    path('signin/',views.signin,name='signin'),
    path('verify_otp/<int:user_id>/',views.verify_otp,name='verify_otp')
]