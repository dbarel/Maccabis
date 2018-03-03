from django.contrib import admin
from .models import Products, Customer, ProductOrderHelper, ListAllOrders, OrdersList, ProductCounter

admin.site.register(Products)
admin.site.register(Customer)
admin.site.register(ProductOrderHelper)
admin.site.register(OrdersList)
admin.site.register(ListAllOrders)
admin.site.register(ProductCounter)
# Register your models here.
