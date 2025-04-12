from django.urls import path
from applications import views
from applications.views import ApplicationsListView

app_name = 'application'
urlpatterns = [
    path('', ApplicationsListView.as_view(), name='applications_list'),
]