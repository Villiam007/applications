from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from applications.models import Product, Order, OrderItem, Category, Favorite, Review
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from applications.owners import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
# Create your views here.

class ProductsListView(OwnerListView):
    model = Product
    template_name = "applications/application_list.html"
    context_object_name = "products"

    def get_queryset(self):
        search_query = self.request.GET.get('search', None)
        category = self.request.GET.get('category', None)

        queryset = Product.objects.all()

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        if category:
            queryset = queryset.filter(category__name=category)

        return queryset

class ProductsDetailView(OwnerDetailView):
    model = Product
    template_name = "applications/application_detail.html"
    context_object_name = "product"

class ProductsCreateView(OwnerCreateView, LoginRequiredMixin):
    model = Product
    template_name = "applications/application_form.html"
    fields = ['title', 'description', 'price', 'stock', 'category']

    def test_func(self):
        # Only staff members can add products
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)