from django.db import models


class Products(models.Model):
    product_name = models.CharField(max_length=50)
    price = models.IntegerField()

    def __str__(self):
        return self.product_name


ACTION_CHOICES = (('p', 'prepared'),
                  ('to', 'taken_orders'),
                  ('tno', 'taken_not_orders'),
                  ('ro', 'returned_orders'))


class ProductCounter(models.Model):
    product_id = models.ForeignKey('Products', on_delete=models.PROTECT)
    number_of_packages = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=15, choices=ACTION_CHOICES)
    owner = models.CharField(max_length=15)


class ProductsSummer(models.Model):
    product_id = models.ForeignKey('Products', on_delete=models.PROTECT)
    product_name = models.CharField(max_length=50)
    sum_ordered = models.IntegerField()
    sum_prepared = models.IntegerField()
    sum_taken = models.IntegerField()
    sum_still_needed_for_orders = models.IntegerField()
    sum_available = models.IntegerField()


class Customer(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)  # convert to regexp (from form?)
    email = models.EmailField(max_length=254, )

    def __str__(self):
        return self.name


class ProductOrderHelper(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE, )
    product_id = models.ForeignKey('Products', on_delete=models.PROTECT)
    number_of_packages = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
    changes = models.CharField(max_length=500)


STATUS_CHOICES = (
    ('0', 'added'),
    ('1', 'confirmed'),
    ('2', 'hereToTake'),
    ('3', 'readyToCheck'),
    ('4', 'readyToPay'),
    ('5', 'done')
)


class OrdersList(models.Model):
    customer_id = models.ForeignKey('Customer', on_delete=models.CASCADE)
    confirmed_time = models.DateTimeField(null=True, blank=True)
    here_to_take_time = models.DateTimeField(null=True, blank=True)
    ready_to_check_time = models.DateTimeField(null=True, blank=True)
    ready_to_pay_time = models.DateTimeField(null=True, blank=True)
    done_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    notes = models.TextField()

    def __str__(self):
        return str(self.id)


class Note(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)
    comment = models.TextField()


class ListAllOrders(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class ListOrdersToConfirm(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class ListOrdersConfirmed(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class ListOrdersHereToTake(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class ListOrdersReadyToCheck(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class ListOrdersReadyToPay(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class ListOrdersDone(models.Model):
    order_id = models.ForeignKey('OrdersList', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class TempOrder(models.Model):
    product_name = models.CharField(max_length=50)
    price = models.IntegerField()
    number_of_packs = models.IntegerField()
