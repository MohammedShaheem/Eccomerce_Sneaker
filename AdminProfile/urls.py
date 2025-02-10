from django.urls import path
from . import views

urlpatterns = [
    path('admin_login/', views.admin_login, name='admin_login'),  
    path('admin_home/', views.home, name='admin_home'), 
    path('category/', views.category, name='category'),
    path('add_category/', views.add_category, name='add_category'),
    path('category/view_category/<int:category_id>/', views.view_category,name='view_category'),
    path('add_products/', views.add_products, name='add_products'),
    path('variance/', views.variance, name='variance'),
    path('admin_users/', views.admin_users, name='admin_users'),
    path('admin_users/admin_users_edit/<int:user_id>/', views.admin_users_edit, name='admin_users_edit'),#getting dynamic user id
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product-detail'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock_user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('edit_product/', views.edit_product, name='edit_product'),
    
    path('products/<int:product_id>/add-variant/', views.add_variant, name='add_variant'),
    
]
