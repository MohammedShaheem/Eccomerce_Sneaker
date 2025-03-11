from django.urls import path
from . import views

urlpatterns = [
    path('admin_login/', views.admin_login, name='admin_login'),  
    path('admin_logout',views.admin_logout,name='admin_logout'),
    path('admin_home/', views.admin_home, name='admin_home'), 
    path('dashboard/sales-data/', views.sales_chart_data, name='sales_chart_data'),
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
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('products/<int:product_id>/add-variant/', views.add_variant, name='add_variant'),
    path('products/<int:variance_id>/single_product_view/', views.single_product_view, name='single_product_view'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('block_category/<int:category_id>/', views.block_category, name='block_category'),
    path('unblock_category/<int:category_id>/', views.unblock_category, name='unblock_category'),
    path('products_edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('product/<int:product_id>/toggle-status/', views.toggle_product_status, name='toggle_product_status'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),
    path('admin-orders/<str:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('edit-variant/<int:variant_id>/', views.edit_variant, name='edit_variant'),
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/add/<str:source>/<int:source_id>/', views.add_offer, name='add_offer'),
    path('offers/edit/<int:offer_id>/', views.edit_offer, name='edit_offer'),
    path('offers/delete/<int:offer_id>/', views.delete_offer, name='delete_offer'),
    path('add-product-offer/<int:product_id>/', views.add_offer, {'source': 'product'}, name='add_product_offer'),
    path('add-category-offer/<int:category_id>/', views.add_offer, {'source': 'category'}, name='add_category_offer'),
    path('create_coupon/',views.create_coupon,name='create_coupon'),
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons-edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('admin-returns/', views.admin_return_requests, name='admin_return_requests'),
    path('adminreturns/<int:request_id>/', views.admin_return_request_detail, name='admin_return_request_detail'),
    path('adminwallettransactions/', views.admin_wallet_transactions, name='admin_wallet_transactions'),
    path('coupons/<int:coupon_id>/delete/', views.delete_coupon, name='delete_coupon'),


]   
    

    

