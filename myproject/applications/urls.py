from django.urls import path
from applications import views
from applications.views import ProductsListView, ProductsCreateView

app_name = 'application'
urlpatterns = [
    path('', ProductsListView.as_view(), name='product_list'),
    path('create/', ProductsCreateView.as_view(), name='create_product'),
    path('<int:pk>/', views.ProductsDetailView.as_view(), name='product_detail'),
    path('update/<int:pk>/', views.ProductsUpdateView.as_view(), name='product_update'),
    path('delete/<int:pk>/', views.ProductsDeleteView.as_view(), name='product_delete'),
    path('category/<str:category>/', ProductsListView.as_view(), name='product_category'),
    path('favorites/<int:pk>', views.FavoriteListView.as_view(), name='favorite_list'),
]