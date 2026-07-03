from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('products/', views.product, name='product'),
    path('products/<slug:category>/', views.product_category, name='product_category'),
    path('products/<slug:category>/<str:node>/', views.product_level2, name='product_level2'),
    path('products/<slug:category>/<slug:sub>/<str:product_id>/', views.product_detail_sub, name='product_detail_sub'),
    path('contact/', views.contact, name='contact'),
    path('distributor/', views.distributor, name='distributor'),
    path('otp/',views.otp,name='otp'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Forgot Password (login page modal — email OTP → new password)
    path('api/forgot-password/send/', views.forgot_password_send, name='forgot_password_send'),
    path('api/forgot-password/verify/', views.forgot_password_verify, name='forgot_password_verify'),
    path('api/forgot-password/reset/', views.forgot_password_reset, name='forgot_password_reset'),

    # Profile (Fix 3)
    path('profile/', views.profile, name='profile'),

    # Cart API (JSON)
    path('api/cart/', views.cart_detail, name='cart_detail'),
    path('api/cart/add/', views.cart_add, name='cart_add'),
    path('api/cart/remove/', views.cart_remove, name='cart_remove'),
    path('api/cart/update/', views.cart_update, name='cart_update'),
    path('api/cart/clear/', views.cart_clear, name='cart_clear'),

    # Back-in-stock notify request
    path('api/notify/', views.notify_request, name='notify_request'),

    # Catalog request (WhatsApp number from home savings calculator)
    path('api/catalog-request/', views.catalog_request, name='catalog_request'),

    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),

    # footer link
    path('privacy_policy', views.privacy_policy, name='privacy_policy'),
    path('terms_condition',views.terms_condition,name='terms_condition'),
    path('refund_return',views.refund_return,name='refund_return'),
    path('shipping_policy',views.shipping_policy,name='shipping_policy'),
    path('services',views.services,name='services'),

    # 404 preview (DEBUG=True me test karne ke liye)
    path('404-preview/', views.preview_404, name='preview_404'),
]
