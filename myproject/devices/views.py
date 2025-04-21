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
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.views.generic.edit import FormView
import json

from .models import (
    Category, Brand, Product, ProductImage, Tag, ProductSpecification,
    UserProfile, Order, OrderItem, Review, Favorite, Cart, CartItem, Coupon, Color, ProductColor
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
        if self.request.user.is_authenticated:
            context['favorite_ids'] = set(
                Favorite.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
        else:
            context['favorite_ids'] = set()
        return context


class AboutView(TemplateView):
    template_name = 'devices/about.html'


class ContactView(FormView):
    template_name = 'devices/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('devices:home')

    def form_valid(self, form):
        # Process the form data (e.g., send email)
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']

        messages.success(self.request, "Thank you for your message! We'll get back to you soon.")
        return super().form_valid(form)


# Product Catalog Views
class CategoryListView(ListView):
    model = Category
    template_name = 'devices/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # กรองเฉพาะหมวดหมู่ Accessory, iOS, และ Windows
        return Category.objects.filter(slug__in=['accessories', 'ios', 'windows'])

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

        # Add color options for iOS products
        if self.object.platform == 'ios':
            context['color_options'] = self.object.colors.all().select_related('color')

        context['related_products'] = Product.objects.filter(category=self.object.category).exclude(id=self.object.id)[:4]

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

        # Calculate rating distribution as a list
        reviews = self.object.reviews.all()
        total_reviews = reviews.count()
        rating_distribution = []

        for i in range(5, 0, -1):  # Iterate from 5 to 1
            count = reviews.filter(rating=i).count()
            percentage = (count / total_reviews) * 100 if total_reviews > 0 else 0
            rating_distribution.append({
                'rating': i,
                'count': count,
                'percentage': round(percentage, 2),  # Round to 2 decimal places
            })

        context['rating_distribution'] = rating_distribution
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
        queryset = Product.objects.filter(platform='ios').order_by('-created_at')
        
        # กรองตามหมวดหมู่
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # กรองตามสี
        color = self.request.GET.get('color')
        if color:
            queryset = queryset.filter(colors__name=color)
        
        # จัดเรียงสินค้า
        sort = self.request.GET.get('sort')
        if sort == 'price-low':
            queryset = queryset.order_by('price')
        elif sort == 'price-high':
            queryset = queryset.order_by('-price')
        elif sort == 'best-selling':
            queryset = queryset.order_by('-sales')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for product in context['products']:
            if product.sale_price and product.price > 0:
                discount = ((product.price - product.sale_price) / product.price) * 100
                # product.discount_percentage = int(discount)
        context['categories'] = Category.objects.filter(
            products__platform='ios'
        ).distinct()
        context['brands'] = Brand.objects.filter(
            products__platform='ios'
        ).distinct()
        context['available_colors'] = Color.objects.filter(
            productcolor__product__platform='ios'
        ).distinct()
        # --- Add this block before return ---
        if self.request.user.is_authenticated:
            context['favorite_ids'] = set(
                Favorite.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
        else:
            context['favorite_ids'] = set()
        # --- End block ---
        return context


# Windows Products Page View
class WindowsProductsView(ListView):
    model = Product
    template_name = 'devices/windows_products.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(platform='windows')
        
        # Filter by category if requested
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by brand if requested
        brand_slugs = self.request.GET.getlist('brand')
        if brand_slugs:
            queryset = queryset.filter(brand__slug__in=brand_slugs)
        
        # Filter by price if requested
        max_price = self.request.GET.get('price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Category-specific filters
        if category_slug == 'gpu':
            gpu_types = self.request.GET.getlist('gpu_type')
            if gpu_types:
                queryset = Product.filter_by_specifications(queryset, 'GPU Type', gpu_types)
        
        elif category_slug == 'ram':
            memory_types = self.request.GET.getlist('memory_type')
            if memory_types:
                queryset = Product.filter_by_specifications(queryset, 'Memory Type', memory_types)
                
            memory_sizes = self.request.GET.getlist('memory_size')
            if memory_sizes:
                queryset = Product.filter_by_specifications(queryset, 'Memory Size', memory_sizes)
        
        elif category_slug == 'ssd':
            ssd_types = self.request.GET.getlist('ssd_type')
            if ssd_types:
                queryset = Product.filter_by_specifications(queryset, 'Interface Type', ssd_types)
                
            capacities = self.request.GET.getlist('capacity')
            if capacities:
                queryset = Product.filter_by_specifications(queryset, 'Capacity', capacities)
        
        elif category_slug == 'hdd':
            capacities = self.request.GET.getlist('capacity')
            if capacities:
                queryset = Product.filter_by_specifications(queryset, 'Capacity', capacities)
        
        # จัดการการเรียงลำดับ (Sort)
        sort_option = self.request.GET.get('sort')
        if sort_option == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_option == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_option == 'name_asc':
            queryset = queryset.order_by('title')
        elif sort_option == 'name_desc':
            queryset = queryset.order_by('-title')
        elif sort_option == 'newest':
            queryset = queryset.order_by('-created_at')

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add available brands for filtering
        context['available_brands'] = Brand.objects.filter(
            products__platform='windows'
        ).distinct()
        
        # Add selected brands
        context['selected_brands'] = self.request.GET.getlist('brand')
        
        # Get current category for title/description
        category_slug = self.request.GET.get('category')
        if category_slug:
            context['current_category'] = Category.objects.filter(slug=category_slug).first()
        
        # Add category-specific filter options
        if category_slug == 'gpu':
            context['gpu_types'] = Product.get_available_specification_values(category_slug, 'GPU Type')
            context['selected_gpu_types'] = self.request.GET.getlist('gpu_type')
        
        elif category_slug == 'ram':
            context['memory_types'] = Product.get_available_specification_values(category_slug, 'Memory Type')
            context['selected_memory_types'] = self.request.GET.getlist('memory_type')
            
            context['memory_sizes'] = Product.get_available_specification_values(category_slug, 'Memory Size')
            context['selected_memory_sizes'] = self.request.GET.getlist('memory_size')
        
        elif category_slug == 'ssd':
            context['ssd_types'] = Product.get_available_specification_values(category_slug, 'Interface Type')
            context['selected_ssd_types'] = self.request.GET.getlist('ssd_type')
            
            context['capacities'] = Product.get_available_specification_values(category_slug, 'Capacity')
            context['selected_capacities'] = self.request.GET.getlist('capacity')
        
        elif category_slug == 'hdd':
            context['capacities'] = Product.get_available_specification_values(category_slug, 'Capacity')
            context['selected_capacities'] = self.request.GET.getlist('capacity')

        # Add selected brands
        context['selected_brands'] = self.request.GET.getlist('brand')
        
        # Add selected sort option
        context['selected_sort'] = self.request.GET.get('sort')
        
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
            return redirect('devices:profile')
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
            return HttpResponseRedirect(reverse('devices:product_detail', args=[product.slug]))

        messages.success(self.request, "Your review has been added successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('devices:product_detail', args=[self.kwargs['slug']])


# Favorites Views
@login_required
@require_POST
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'created': created,
            'message': 'Added to favorites!' #if created else 'Already in favorites'
        })

    messages.success(request, "Product added to your favorites!")
    return redirect('devices:product_detail', slug=product.slug)


@login_required
@require_POST
def remove_from_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.filter(user=request.user, product=product).delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Removed from favorites'
        })

    messages.success(request, "Product removed from your favorites.")
    return redirect('devices:favorites')

@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'devices/favorites.html', {'favorites': favorites})


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
        'cart_items': items,
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

    if request.content_type == 'application/json':
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        color_id = data.get('color')
    else:
        quantity = int(request.POST.get('quantity', 1))
        color_id = request.POST.get('color')

    # Get color selection if it's an iOS product
    product_color = None
    if product.platform == 'ios' and product.has_color_options:
        color_id = request.POST.get('color')
        if color_id:
            product_color = get_object_or_404(ProductColor, id=color_id, product=product)

    # Use filter().first() to avoid MultipleObjectsReturned
    cart_item = CartItem.objects.filter(
        cart=cart,
        product=product,
        product_color=product_color
    ).first()

    if cart_item:
        cart_item.quantity += quantity
        cart_item.save()
        created = False
    else:
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            product_color=product_color,
            quantity=quantity
        )
        created = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'created': created,
            'message': f"{product.title} added to your cart",
            'cart_total': cart.total_items
        })

    messages.success(request, f"{product.title} added to your cart!")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

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

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'cart_total': cart_item.cart.total_items,
            'item_subtotal': cart_item.subtotal if quantity > 0 else 0,
            'cart_subtotal': cart_item.cart.total_price
        })

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed from cart',
            'cart_total': cart_item.cart.total_items,
            'cart_subtotal': cart_item.cart.total_price
        })

    messages.success(request, "Item removed from cart.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


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
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

                # Check if cart meets minimum purchase requirement
                cart = Cart.objects.get(user=request.user)
                if cart.total_price < coupon.min_purchase:
                    messages.error(
                        request,
                        f"Your order total must be at least ${coupon.min_purchase} to use this coupon."
                    )
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

                # devices coupon in session
                request.session['coupon_id'] = coupon.id
                messages.success(request, "Coupon applied successfully!")

            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


# Checkout and Order Views
class CheckoutView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'devices/checkout.html'
    success_url = reverse_lazy('devices:order_confirmation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's cart
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        items = cart.items.select_related('product').all()

        if not items:
            messages.warning(self.request, "Your cart is empty!")
            return self.render_to_response(self.get_context_data(form=self.get_form()))

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
            return self.render_to_response(self.get_context_data(form=form))  # Stay on the current page

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
                product_color=cart_item.product_color,
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

# Add these authentication views
class LoginView(TemplateView):
    template_name = 'devices/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AuthenticationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                # Always redirect to home page after login
                return redirect('devices:home')
        messages.error(request, "Invalid username or password.")
        return render(request, self.template_name, {'form': form})
    
    import logging
    logging.basicConfig(level=logging.DEBUG)


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy('devices:home')  # Redirect to the home page

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)
class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'devices/profile.html'
    fields = ['avatar']
    success_url = reverse_lazy('devices:profile')

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(user=self.request.user).order_by('-created_at')[:5]
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)