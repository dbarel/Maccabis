from django.shortcuts import redirect
from django.db.models import Sum, Q
from django.views.generic import DetailView, ListView
from .models import OrdersList, Customer, ProductOrderHelper, Products, ProductCounter, ProductsSummer
import datetime
# import pdb

ACTIONS_CHOICES = {0: 'Confirm',
                   1: 'GoToFridge',
                   2: 'FinishedFridge',
                   3: 'Checked',
                   4: 'Done',
                   5: 'Nothing'}


class OrderDetailView(DetailView):
    model = OrdersList
    template_name = "orders/order.html"

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context["customer"] = Customer.objects.get(id=self.object.customer_id.id)
        context["products_in_order"] = ProductOrderHelper.objects.filter(order_id=self.object.id).order_by('product_id__id')
        temp_objects = ProductOrderHelper.objects.filter(order_id=self.object.id)
        # .aggregate(total=Sum('progress', field="progress*estimated_days"))['total'])
        total = 0
        for obj in temp_objects:
            total = total+ obj.number_of_packages * obj.product_id.price
        context["total_price"] = total
        # action (according to status):
        self.object = self.get_object()  # change to this_object?
        status_int = int(self.object.status)
        print("order status: ", status_int)

        context["action"] = ACTIONS_CHOICES[status_int]
        context["comment"] = self.object.notes

        # set classes:
        context["confirmed_class"] = "notDone"
        context["here_to_take_class"] = "notDone"
        context["ready_to_check_class"] = "notDone"
        context["ready_to_pay_class"] = "notDone"
        context["done_class"] = "notDone"
        if status_int > 0:
            context["confirmed_class"] = "done"
            if status_int > 1:
                context["here_to_take_class"] = "done"
                if status_int > 2:
                    context["ready_to_check_class"] = "done"
                    if status_int > 3:
                        context["ready_to_pay_class"] = "done"
                        if status_int > 4:
                            context["done_class"] = "done"

        if self.object.take_on_friday:
            context["b_take_on_friday"] = True
        else:
            context["b_take_on_friday"] = False
        if self.object.delivery:
            context["delivery"] = True
        else:
            context["delivery"] = False
        if self.object.for_second_holiday:
            context["b_second_holiday"] = True
        else:
            context["b_second_holiday"] = False

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # what was the action?
        print(request.POST)
        status_int_old = int(self.object.status)
        print("old status: ", str(status_int_old))
        if 'GoToNextStep' in request.POST:
            # self.object.confirmed_time = datetime.datetime.now()
            status_str_new = str(min(5, status_int_old + 1))
            self.object.status = status_str_new
            print("in GoToNextStep - order status: ", self.object.status)
            self.object.save()
            set_status_time(self.object, status_str_new)

            # print("GoToNextStep time:", self.object.confirmed_time,  type(self.object), type(self.object.confirmed_time))

            if status_int_old == 2:
                # if this was for finishedFridge (status was 2 (hereToTake) and now is 3 (readyToCheck) ) -
                # remove the products from inventory:
                remove_order_from_inventory(self.object)

            return redirect_to_list(status_int_old)

        if 'GoToPrevStep' in request.POST:
            status_str_new = str(max(0, status_int_old - 1))
            self.object.status = status_str_new
            print("in GoToPrevStep - order status: ", self.object.status)
            self.object.save()
            set_status_time(self.object, status_str_new)
            # print("GoToNextStep time:", self.object.confirmed_time,  type(self.object), type(self.object.confirmed_time))

            if status_int_old == 3:
                # if status was 3 (readyToCheck) and now is 2 (hereToTake)
                # restore the products to inventory (delete lines of 'taken' from counter):
                restore_order_to_inventory(self.object)

            return redirect_to_list(status_int_old)

        if 'editOrder' in request.POST:
            this_order = self.get_object().id
            request.session['order_num'] = this_order
            if status_int_old > 2: # ready to check or higher
                edit_inventory = True
            else:
                edit_inventory = False
            request.session['edit_inventory'] = edit_inventory
            return redirect('../editOrder/')


class ListViewOrdersList(ListView):
    model = OrdersList
    template_name = "orders/orders_list.html"

    def get_context_data(self, **kwargs):
        context = super(ListViewOrdersList, self).get_context_data(**kwargs)
        context["list_title"] = get_title(self.kwargs['status'])
        if self.kwargs['status'] == 'all':
            context["orders_list"] = OrdersList.objects.filter(take_on_friday=False, delivery=False)\
                .order_by("foreign_order_id") \
                .values('id', 'foreign_order_id', 'customer_id__name', 'notes')
            context["orders_list_2"] = OrdersList.objects.filter(take_on_friday=True, delivery=False)\
                .order_by("foreign_order_id") \
                .values('id', 'foreign_order_id', 'customer_id__name', 'notes')
            context["orders_list_3"] = OrdersList.objects.filter(delivery=True)\
                .order_by("foreign_order_id") \
                .values('id', 'foreign_order_id', 'customer_id__name', 'notes')
            context["orders_list_4"] = OrdersList.objects.filter(for_second_holiday=True)\
                .order_by("foreign_order_id") \
                .values('id', 'foreign_order_id', 'customer_id__name', 'notes')
        else:
            # context["orders_list"] = OrdersList.objects.filter(status=self.kwargs['status']).order_by("id")\
            #      .values('id', 'customer_id__name')
            status_int = self.kwargs['status']

            temp_list = OrdersList.objects.filter(status=status_int, take_on_friday=False, delivery=False)\
                .values('id', 'foreign_order_id', 'customer_id__name', 'notes')
            sorted_list = sort_by_status_time(temp_list, status_int)
            context["orders_list"] = sorted_list

            temp_list = OrdersList.objects.filter(status=status_int, take_on_friday=True, delivery=False)\
                .values('id', 'foreign_order_id', 'customer_id__name', 'notes')
            sorted_list = sort_by_status_time(temp_list, status_int)
            context["orders_list_2"] = sorted_list

            temp_list = OrdersList.objects.filter(status=status_int, delivery=True).values('id', 'foreign_order_id',
                                                                            'customer_id__name', 'notes')
            sorted_list = sort_by_status_time(temp_list, status_int)
            context["orders_list_3"] = sorted_list

            temp_list = OrdersList.objects.filter(status=status_int, for_second_holiday=True).values('id', 'foreign_order_id',
                                                                            'customer_id__name', 'notes')
            sorted_list = sort_by_status_time(temp_list, status_int)
            context["orders_list_4"] = sorted_list

        context["link_page_name"] = 'orders'
        return context


class ListViewCustomersList(ListView):
    model = Customer
    template_name = "orders/customers_list.html"

    def get_context_data(self, **kwargs):
        context = super(ListViewCustomersList, self).get_context_data(**kwargs)
        context["list_title"] = "Existing customers list"
        context["customers_list"] = Customer.objects.all().order_by("name")
        context["link_page_name"] = 'newOrder'
        return context


class ListViewProducts(ListView):
    model = Products
    template_name = "orders/products_summary.html"

    def get_context_data(self, **kwargs):
        context = super(ListViewProducts, self).get_context_data(**kwargs)
        context["list_title"] = 'Products summary'
        # summing:
        all_products = Products.objects.all()
        all_orders_lines = ProductOrderHelper.objects.all()
        all_products_count_lines = ProductCounter.objects.all()

        ProductsSummer.objects.all().delete()
        for product in all_products:
            # ordered:
            temp = all_orders_lines.filter(product_id=product).aggregate(Sum('number_of_packages'))
            val_ordered = temp['number_of_packages__sum']
            val_ordered = int(0 if val_ordered is None else val_ordered)
            # sum_ordered.append(val_ordered)

            # prepared:
            temp = all_products_count_lines.filter(product_id=product, action='p').aggregate(Sum('number_of_packages'))
            val_prepared = temp['number_of_packages__sum']
            val_prepared = int(0 if val_prepared is None else val_prepared)
            # sum_prepared.append(val_prepared)

            # need to be prepared:
            val_need_to_prepare = val_ordered - val_prepared

            # taken (for orders, and other):
            # here I can count the lines in all_orders_lines, with orders that are in status 3-5...
            temp = all_products_count_lines.filter(product_id=product, action='to').aggregate(Sum('number_of_packages'))
            val_taken_for_orders = temp['number_of_packages__sum']
            val_taken_for_orders = int(0 if val_taken_for_orders is None else val_taken_for_orders)
            temp = all_products_count_lines.filter(product_id=product, action='tno').aggregate(Sum('number_of_packages'))
            val_taken_not_orders = temp['number_of_packages__sum']
            val_taken_not_orders = int(0 if val_taken_not_orders is None else val_taken_not_orders)
            val_taken = val_taken_for_orders + val_taken_not_orders
            # sum_taken.append(val_taken)

            # still needed for orders: (two ways to check)
            # 1) by counting all the lines with orders that are in status 0-3
            # (maybe later)

            # 2) sum_orders - sum_taken_for_orders
            val_needed = val_ordered - val_taken_for_orders
            # sum_needed_for_orders.append(val_needed)

            # available:
            val_available = val_prepared - val_taken
            # sum_available.append(val_available)

            # extras:
            val_extras = val_available - val_needed

            # put in model:
            this_product_sum = ProductsSummer(product_id=product, product_name=str(product),
                                              sum_ordered=val_ordered, sum_prepared=val_prepared,
                                              sum_taken=val_taken, sum_still_needed_for_orders=val_needed,
                                              sum_available=val_available,
                                              sum_still_need_to_prepare=val_need_to_prepare,
                                              sum_extras=val_extras)
            this_product_sum.save()

        context["Products_list"] = ProductsSummer.objects.all()
        return context


def redirect_to_list(list_num):
    if list_num == 0:
        return redirect('../list_to_confirm/')
    if list_num == 1:
        return redirect('../list_confirmed/')
    if list_num == 2:
        return redirect('../list_here_to_take/')
    if list_num == 3:
        return redirect('../list_ready_to_check/')
    if list_num == 4:
        return redirect('../list_ready_to_pay/')
    if list_num == 5:
        return redirect('../list_done/')


def get_title(list_num):
    if list_num == '0':
        return 'orders to confirm'
    if list_num == '1':
        return 'orders confirmed'
    if list_num == '2':
        return 'orders waiting for fridge'
    if list_num == '3':
        return 'orders ready to be checked'
    if list_num == '4':
        return 'orders ready to pay'
    if list_num == '5':
        return 'orders done'


def remove_order_from_inventory(order):
    print("removing order ", order, " from inventory")

    # get order products:
    products_in_order = ProductOrderHelper.objects.filter(order_id=order.id)

    # set new line for each product:
    owner_str = "order_id_" + str(order)

    for product in products_in_order:
        new_line = ProductCounter(product_id=product.product_id, number_of_packages=product.number_of_packages,
                                  time=datetime.datetime.now(), action='to', owner=owner_str)
        print("removing product ", product.product_id, ", ", product.number_of_packages, " packs, ", owner_str)
        new_line.save()


def restore_order_to_inventory(order):
    print("restoring order ", order, " to inventory")

    owner_str = "order_id_" + str(order)
    ProductCounter.objects.filter(owner=owner_str).delete()


def sort_by_status_time(temp_list, status_str):
    if status_str == '0':
        return temp_list.order_by("id")
    if status_str == '1':
        return temp_list.order_by("id")
    if status_str == '2':
        return temp_list.order_by("here_to_take_time")
    if status_str == '3':
        return temp_list.order_by("ready_to_check_time")
    if status_str == '4':
        return temp_list.order_by("ready_to_pay_time")
    if status_str == '5':
        return temp_list.order_by("done_time")


def set_status_time(this_order, status_str):
    time_now = datetime.datetime.now()
    if status_str == '0':
        return
    if status_str == '1':
        this_order.confirmed_time = time_now
        this_order.save()
        return
    if status_str == '2':
        this_order.here_to_take_time = time_now
        this_order.save()
        return
    if status_str == '3':
        this_order.ready_to_check_time = time_now
        this_order.save()
        return
    if status_str == '4':
        this_order.ready_to_pay_time = time_now
        this_order.save()
        return
    if status_str == '5':
        this_order.done_time = time_now
        this_order.save()
        return

