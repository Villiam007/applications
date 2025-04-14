from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy, reverse

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

class ProductsCreateView(LoginRequiredMixin, UserPassesTestMixin, OwnerCreateView):
    model = Product
    template_name = "applications/application_form.html"
    fields = ['title', 'description', 'price', 'stock', 'category']

    def test_func(self):
        # Only staff members can add products
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    
class ProductsUpdateView(LoginRequiredMixin, UserPassesTestMixin, OwnerUpdateView):
    model = Product
    fields = ['title', 'price', 'description', 'stock', 'category', 'picture']
    template_name = 'applications/application_form.html'
    success_url = reverse_lazy('applications:product_list')

    def test_func(self):
        # Only staff members can update products
        return self.request.user.is_staff

    def get(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        form = CreateForm(instance=product)
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        product = get_object_or_404(Product, id=pk)
        form = CreateForm(request.POST, request.FILES or None, instance=product)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        product = form.save(commit=False)
        product.save()

        return redirect(self.success_url)

class ProductsDeleteView(LoginRequiredMixin, UserPassesTestMixin, OwnerDeleteView):
    model = Product
    template_name = "applications/application_delete.html"
    success_url = reverse_lazy('applications:product_list')

    def test_func(self):
        # Only staff members can delete products
        return self.request.user.is_staff