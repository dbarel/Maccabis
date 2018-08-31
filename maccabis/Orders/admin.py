from django.contrib import admin
from .models import Products, Customer, ProductOrderHelper, OrdersList, ProductCounter

from django.contrib import admin
from .models import Products, Customer, ProductOrderHelper, OrdersList, ProductCounter, ProductsSummer


class ProductOrderHelperAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'product_id', 'number_of_packages')
    list_filter = ('order_id', 'product_id')


def get_order(self, obj):
    return obj.order_id.foreign_order_id


admin.site.register(Products)
admin.site.register(Customer)
admin.site.register(ProductOrderHelper, ProductOrderHelperAdmin)
admin.site.register(OrdersList)
admin.site.register(ProductCounter)
admin.site.register(ProductsSummer)
# Register your models here.
