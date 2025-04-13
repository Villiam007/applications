from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q

from applications.models import Product, Order, OrderItem, Category, Favorite, Review
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from applications.owners import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from applications.forms import CreateForm
# Create your views here.

class ProductsListView(OwnerListView):
    model = Product
    template_name = "applications/application_list.html"
    context_object_name = "products"

    def get_queryset(self):
        category = self.request.GET.get('category', None)
        if category:
            return Product.objects.filter(category__name=category)
        return Product.objects.all()

class ProductsDetailView(OwnerDetailView):
    model = Product
    template_name = "applications/application_detail.html"
    context_object_name = "product"

class ProductsCreateView(UserPassesTestMixin, OwnerCreateView):
    model = Product
    template_name = "applications/application_form.html"
    fields = ['title', 'description', 'price', 'stock', 'category']

    def test_func(self):
        # Only staff members can add products
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    
class ProductsUpdateView(UpdateView):
    pass

class ProductsDeleteView(DeleteView):
    pass

class FavoriteListView(LoginRequiredMixin, ListView):
    pass