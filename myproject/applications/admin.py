from django.contrib import admin
from applications.models import Product

# Register your models here.

class PicAdmin(admin.ModelAdmin):
    exclude=('picture', 'content_type')

admin.site.register(Product, PicAdmin)
