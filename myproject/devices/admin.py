from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, ProductImage, Tag, ProductSpecification,
    UserProfile, Order, OrderItem, Review, Favorite, Cart, CartItem, Coupon,
    Color, ProductColor
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
        return "No Image"
    
    image_preview.short_description = 'Preview'

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 3

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'price']
    extra = 0
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'featured', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['featured']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'website']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_filter = ['name']

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code']
    search_fields = ['name', 'hex_code']

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'stock', 'is_default']
    list_filter = ['product', 'color', 'is_default']
    search_fields = ['product__title', 'color__name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'sale_price', 'category', 'brand', 'stock', 'is_featured', 'is_new', 'is_bestseller']
    list_filter = ['category', 'brand', 'platform', 'is_featured', 'is_new', 'is_bestseller']
    search_fields = ['title', 'description', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['tags', 'colors']
    inlines = [ProductImageInline, ProductSpecificationInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'main_image')
        }),
        ('Pricing and Inventory', {
            'fields': ('price', 'sale_price', 'stock')
        }),
        ('Categorization', {
            'fields': ('category', 'brand', 'platform', 'tags')
        }),
        ('Features', {
            'fields': ('is_featured', 'is_new', 'is_bestseller')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'image_preview']
    list_filter = ['is_primary', 'product__category']
    search_fields = ['product__title', 'alt_text']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
        return "No Image"
    
    image_preview.short_description = 'Preview'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'city', 'country']
    search_fields = ['user__username', 'user__email', 'phone_number', 'city', 'country']
    list_filter = ['country', 'city']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_method', 'total_price', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_address']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'order_number', 'status', 'payment_method')
        }),
        ('Shipping Details', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_country', 'shipping_postal_code', 'tracking_number')
        }),
        ('Billing Details', {
            'fields': ('billing_address', 'billing_city', 'billing_country', 'billing_postal_code')
        }),
        ('Financial Details', {
            'fields': ('total_price', 'shipping_cost', 'discount')
        }),
        ('Other Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product__title']
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'title', 'created_at', 'helpful_votes']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'product__title', 'title', 'text']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__title']
    readonly_fields = ['created_at']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'subtotal', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__username', 'product__title']
    readonly_fields = ['subtotal', 'added_at']
    
    def subtotal(self, obj):
        return obj.subtotal
    
    subtotal.short_description = 'Subtotal'

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_display', 'is_active', 'valid_from', 'valid_to', 'times_used']
    list_filter = ['is_active', 'valid_from', 'valid_to']
    search_fields = ['code', 'description']
    
    def discount_display(self, obj):
        if obj.discount_amount:
            return f"${obj.discount_amount}"
        elif obj.discount_percentage:
            return f"{obj.discount_percentage}%"
        return "-"
    
    discount_display.short_description = 'Discount'