from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings

from .models import (
    Category, Brand, Product, ProductImage, Tag, ProductSpecification,
    UserProfile, Order, OrderItem, Review, Favorite, Cart, CartItem, Coupon
)
from .forms import (
    ReviewForm, UserProfileForm, OrderForm, ProductSearchForm, ContactForm,
    CouponForm
)


# Home and General Views
class HomeView(TemplateView):
    template_name = 'devices/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(is_featured=True)[:8]
        context['new_products'] = Product.objects.filter(is_new=True).order_by('-created_at')[:8]
        context['bestsellers'] = Product.objects.filter(is_bestseller=True)[:8]
        context['categories'] = Category.objects.filter(featured=True)[:6]
        return context


class AboutView(TemplateView):
    template_name = 'devices/about.html'


class ContactView(CreateView):
    template_name = 'devices/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact_success')

    def form_valid(self, form):
        # Process the form data (e.g., send email)
        messages.success(self.request, "Thank you for your message! We'll get back to you soon.")
        return super().form_valid(form)


# Product Catalog Views
class CategoryListView(ListView):
    model = Category
    template_name = 'devices/category_list.html'
    context_object_name = 'categories'


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'devices/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.object.products.all()

        # Filtering
        platform = self.request.GET.get('platform')
        if platform:
            products = products.filter(platform=platform)

        brand = self.request.GET.get('brand')
        if brand:
            products = products.filter(brand__slug=brand)

        # Sorting
        sort = self.request.GET.get('sort', '-created_at')  # Default to newest
        if sort == 'price_low':
            products = products.order_by('price')
        elif sort == 'price_high':
            products = products.order_by('-price')
        elif sort == 'name':
            products = products.order_by('title')
        else:
            products = products.order_by(sort)

        # Pagination
        paginator = Paginator(products, 12)  # 12 products per page
        page_number = self.request.GET.get('page')
        context['products'] = paginator.get_page(page_number)

        # Filter options
        context['brands'] = Brand.objects.filter(
            products__category=self.object
        ).distinct()

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'devices/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.images.all()
        context['specifications'] = self.object.specifications.all()
        context['reviews'] = self.object.reviews.all()
        context['related_products'] = Product.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:4]

        # Check if product is in user's favorites
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, product=self.object
            ).exists()

            # Add review form if user hasn't reviewed yet
            has_reviewed = Review.objects.filter(
                user=self.request.user, product=self.object
            ).exists()
            if not has_reviewed:
                context['review_form'] = ReviewForm()

        return context


class ProductSearchView(ListView):
    model = Product
    template_name = 'devices/search_results.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query) |
                Q(tags__name__icontains=query) |
                Q(category__name__icontains=query) |
                Q(brand__name__icontains=query)
            ).distinct()

        # Apply filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)

        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand__slug=brand)

        # Price range filter
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'name':
            queryset = queryset.order_by('title')
        else:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        context['total_results'] = self.get_queryset().count()
        return context


# iOS Products Page View
class IOSProductsView(ListView):
    model = Product
    template_name = 'devices/ios_products.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(platform='ios').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            products__platform='ios'
        ).distinct()
        context['brands'] = Brand.objects.filter(
            products__platform='ios'
        ).distinct()
        return context


# Windows Products Page View
class WindowsProductsView(ListView):
    model = Product
    template_name = 'devices/windows_products.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(platform='windows').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            products__platform='windows'
        ).distinct()
        context['brands'] = Brand.objects.filter(
            products__platform='windows'
        ).distinct()
        return context


# Accessories Page View
class AccessoriesView(ListView):
    model = Product
    template_name = 'devices/accessories.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(
            category__name__icontains='accessory'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            name__icontains='accessory'
        ).distinct()
        context['brands'] = Brand.objects.filter(
            products__category__name__icontains='accessory'
        ).distinct()
        return context


# User Authentication & Profile Views
@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Get user's favorites
    favorites = Favorite.objects.filter(user=request.user).select_related('product')

    # Get user's reviews
    reviews = Review.objects.filter(user=request.user).select_related('product')

    context = {
        'form': form,
        'orders': orders,
        'favorites': favorites,
        'reviews': reviews,
    }

    return render(request, 'devices/profile.html', context)


# Review Views
class AddReviewView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm

    def form_valid(self, form):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        form.instance.product = product
        form.instance.user = self.request.user

        # Check if user already reviewed this product
        existing_review = Review.objects.filter(
            user=self.request.user, product=product
        ).first()

        if existing_review:
            messages.warning(self.request, "You have already reviewed this product.")
            return HttpResponseRedirect(reverse('product_detail', args=[product.slug]))

        messages.success(self.request, "Your review has been added successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('product_detail', args=[self.kwargs['slug']])


# Favorites Views
@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)

    if request.is_ajax():
        return JsonResponse({
            'status': 'success',
            'created': created,
            'message': 'Added to favorites' if created else 'Already in favorites'
        })

    messages.success(request, "Product added to your favorites!")
    return redirect('product_detail', slug=product.slug)


@login_required
def remove_from_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.filter(user=request.user, product=product).delete()

    if request.is_ajax():
        return JsonResponse({
            'status': 'success',
            'message': 'Removed from favorites'
        })

    messages.success(request, "Product removed from your favorites.")
    return redirect('profile')


# Cart Views
@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()

    # Check for applied coupon
    coupon_id = request.session.get('coupon_id')
    coupon = None
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
        except Coupon.DoesNotExist:
            request.session.pop('coupon_id', None)

    # Calculate totals
    subtotal = sum(item.product.price * item.quantity for item in items)

    # Apply discount if coupon exists
    discount = 0
    if coupon:
        if coupon.discount_amount:
            discount = coupon.discount_amount
        elif coupon.discount_percentage:
            discount = subtotal * (coupon.discount_percentage / 100)

    # Shipping cost (simplified example)
    shipping_cost = 0 if subtotal > 100 else 10

    # Total
    total = subtotal - discount + shipping_cost

    context = {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'shipping_cost': shipping_cost,
        'total': total,
        'coupon': coupon,
        'coupon_form': CouponForm(),
    }

    return render(request, 'devices/cart.html', context)


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    if request.is_ajax():
        return JsonResponse({
            'status': 'success',
            'message': f"{product.title} added to your cart",
            'cart_total': cart.total_items
        })

    messages.success(request, f"{product.title} added to your cart!")
    return redirect('cart_detail')


@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated successfully.")
    else:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")

    if request.is_ajax():
        return JsonResponse({
            'status': 'success',
            'cart_total': cart_item.cart.total_items,
            'item_subtotal': cart_item.subtotal if quantity > 0 else 0,
            'cart_subtotal': cart_item.cart.total_price
        })

    return redirect('cart_detail')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    if request.is_ajax():
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed from cart',
            'cart_total': cart_item.cart.total_items,
            'cart_subtotal': cart_item.cart.total_price
        })

    messages.success(request, "Item removed from cart.")
    return redirect('cart_detail')


@login_required
def apply_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']

            try:
                coupon = Coupon.objects.get(
                    code__iexact=code,
                    is_active=True,
                    valid_from__lte=timezone.now(),
                    valid_to__gte=timezone.now()
                )

                # Check if coupon has usage limit
                if coupon.uses_limit and coupon.times_used >= coupon.uses_limit:
                    messages.error(request, "This coupon has reached its usage limit.")
                    return redirect('cart_detail')

                # Check if cart meets minimum purchase requirement
                cart = Cart.objects.get(user=request.user)
                if cart.total_price < coupon.min_purchase:
                    messages.error(
                        request,
                        f"Your order total must be at least ${coupon.min_purchase} to use this coupon."
                    )
                    return redirect('cart_detail')

                # devices coupon in session
                request.session['coupon_id'] = coupon.id
                messages.success(request, "Coupon applied successfully!")

            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")

    return redirect('cart_detail')


# Checkout and Order Views
class CheckoutView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'devices/checkout.html'
    success_url = reverse_lazy('order_confirmation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's cart
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        items = cart.items.select_related('product').all()

        if not items:
            messages.warning(self.request, "Your cart is empty!")
            return HttpResponseRedirect(reverse('cart_detail'))

        # Check for applied coupon
        coupon_id = self.request.session.get('coupon_id')
        coupon = None
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, is_active=True, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
            except Coupon.DoesNotExist:
                self.request.session.pop('coupon_id', None)

        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in items)

        # Apply discount if coupon exists
        discount = 0
        if coupon:
            if coupon.discount_amount:
                discount = coupon.discount_amount
            elif coupon.discount_percentage:
                discount = subtotal * (coupon.discount_percentage / 100)

        # Shipping cost (simplified example)
        shipping_cost = 0 if subtotal > 100 else 10

        # Total
        total = subtotal - discount + shipping_cost

        # Add to context
        context['cart'] = cart
        context['items'] = items
        context['subtotal'] = subtotal
        context['discount'] = discount
        context['shipping_cost'] = shipping_cost
        context['total'] = total
        context['coupon'] = coupon

        # Pre-fill form with user profile data if available
        try:
            profile = self.request.user.profile
            initial_data = {
                'shipping_address': profile.address,
                'shipping_city': profile.city,
                'shipping_country': profile.country,
                'shipping_postal_code': profile.postal_code,
            }
            context['form'] = OrderForm(initial=initial_data)
        except:
            pass

        return context

    def form_valid(self, form):
        # Associate order with current user
        form.instance.user = self.request.user

        # Get cart items
        cart = Cart.objects.get(user=self.request.user)
        items = cart.items.select_related('product').all()

        if not items:
            messages.warning(self.request, "Your cart is empty!")
            return HttpResponseRedirect(reverse('cart_detail'))

        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in items)

        # Apply coupon if exists
        coupon_id = self.request.session.get('coupon_id')
        discount = 0
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                if coupon.discount_amount:
                    discount = coupon.discount_amount
                elif coupon.discount_percentage:
                    discount = subtotal * (coupon.discount_percentage / 100)

                # Update coupon usage
                coupon.times_used += 1
                coupon.save()

                # Clear coupon from session
                self.request.session.pop('coupon_id', None)

                # Set discount on order
                form.instance.discount = discount

            except Coupon.DoesNotExist:
                pass

        # Set shipping cost
        form.instance.shipping_cost = 0 if subtotal > 100 else 10

        # Set total price
        form.instance.total_price = subtotal - discount + form.instance.shipping_cost

        # Save order first to generate ID
        response = super().form_valid(form)

        # Now create order items
        for cart_item in items:
            OrderItem.objects.create(
                order=self.object,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

            # Update product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        # Empty the cart
        cart.items.all().delete()

        # devices order ID in session for confirmation page
        self.request.session['last_order_id'] = self.object.id

        return response


class OrderConfirmationView(LoginRequiredMixin, TemplateView):
    template_name = 'devices/order_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.session.get('last_order_id')

        if order_id:
            context['order'] = get_object_or_404(Order, id=order_id, user=self.request.user)
            # Clear it from session
            self.request.session.pop('last_order_id', None)
        else:
            # Redirect if no order found
            return HttpResponseRedirect(reverse('home'))

        return context


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'devices/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'devices/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)