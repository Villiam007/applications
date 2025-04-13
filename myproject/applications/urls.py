from django.urls import path
from applications import views
from applications.views import ProductsListView

app_name = 'application'
urlpatterns = [
    path('', ProductsListView.as_view(), name='applications_list'),
]