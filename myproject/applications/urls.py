from django.urls import path
from . import views

urlpatterns = [
    # Home and General Views
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/success/', views.TemplateView.as_view(template_name='store/contact_success.html'), name='contact_success'),
    
    # Product Catalog Views
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('search/', views.ProductSearchView.as_view(), name='product_search'),
    
    # Platform-specific Product Views
    path('ios-products/', views.IOSProductsView.as_view(), name='ios_products'),
    path('windows-products/', views.WindowsProductsView.as_view(), name='windows_products'),
    path('accessories/', views.AccessoriesView.as_view(), name='accessories'),
    
    # User Authentication & Profile Views
    path('profile/', views.profile_view, name='profile'),
    
    # Review Views
    path('product/<slug:slug>/add-review/', views.AddReviewView.as_view(), name='add_review'),
    
    # Favorites Views
    path('favorites/add/<int:product_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:product_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    
    # Cart Views
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    
    # Checkout and Order Views
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order/confirmation/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]