from django.shortcuts import redirect
from django.db.models import Sum, Q
from django.views.generic import DetailView, ListView
from .models import OrdersList, Customer, ProductOrderHelper, Products, ProductCounter, ProductsSummer
import datetime
# import pdb

all_deliveries_methods = ["איסוף עצמי ביום חמישי",
                          "איסוף עצמי ביום שישי",
                          "משלוח ביום חמישי",
                          "משלוח ביום שישי",
                          "משלוח מחוץ למודיעין"]

ACTIONS_CHOICES = { 1: 'עבור_למקרר',
                    2: 'נאסף',
                    3: 'נאסף',
                    4: 'נבדק',
                    5: 'נבדק',
                    6: 'הסתיים',
                    7: 'כלום'}

BACK_ACTIONS_CHOICES = {1: 'כלום',
                        2: 'עוד לא הגיעו',
                        3: 'עוד לא הגיעו',
                        4: 'המתנה למקרר',
                        5: 'המתנה למקרר',
                        6: 'המתנה לבדיקה',
                        7: 'המתנה לתשלום'}

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

        # check if total is the same as total in ordersList
        # (this is temporary to make sure we can use total in ordersList)
        if total != self.object.total_price:
            print("!!!!!!!!!! total is different from total in orderslist: ", total, " vs ", self.object.total_price)


        context["total_price"] = total
        # action (according to status):
        self.object = self.get_object()  # change to this_object?
        status_int = int(self.object.status)
        print("order status: ", status_int)

        # if current status is 2 (waiting for frig)
        # we turn it to 3 (preparing in frig) while inside the order/
        # same for status 4 (ready to check) and 5 (checking)
        # if status_int == 2:
        #     status_int = 3
        # if status_int == 4:
        #     status_int = 5

        status_str_new = str(status_int)
        self.object.status = status_str_new

        self.object.save()

        context["action"] = ACTIONS_CHOICES[status_int]
        context["back_action"] = BACK_ACTIONS_CHOICES[status_int]
        context["comment"] = self.object.notes

        # set classes:
        context["confirmed_class"] = "notDone"
        context["here_to_take_class"] = "notDone"
        context["preparing_class"] = "notDone"
        context["ready_to_check_class"] = "notDone"
        context["checking_class"] = "notDone"
        context["ready_to_pay_class"] = "notDone"
        context["done_class"] = "notDone"
        if status_int > 1:
            context["confirmed_class"] = "done"
            if status_int > 2:
                context["here_to_take_class"] = "done"
                if status_int > 3:
                    context["preparing_class"] = "done"
                    if status_int > 4:
                        context["ready_to_check_class"] = "done"
                        if status_int > 5:
                            context["checking_class"] = "done"
                            if status_int > 6:
                                context["ready_to_pay_class"] = "done"
                                if status_int > 7:
                                    context["done_class"] = "done"

        # if self.object.take_on_friday:
        #     context["b_take_on_friday"] = True
        # else:
        #     context["b_take_on_friday"] = False
        if self.object.pre_prepared:
            context["b_pre_prepared"] = True
        else:
            context["b_pre_prepared"] = False
        if self.object.delivery_method == 3 | self.object.delivery_method == 4:
            context["delivery"] = True
        else:
            context["delivery"] = False
        if self.object.payed:
            context["b_payed"] = True
        else:
            context["b_payed"] = False
        # if self.object.for_second_holiday:
        #     context["b_second_holiday"] = True
        # else:
        #     context["b_second_holiday"] = False

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # what was the action?
        print(request.POST)
        status_int_old = int(self.object.status)

        # reversing what we did in get_context_data() for status 2/4
        # if status_int_old == 3:
        #     status_int_old = 2
        # if status_int_old == 5:
        #     status_int_old = 4

        print("old status: ", str(status_int_old))
        if 'GoToNextStep' in request.POST:
            text = request.POST.get("GoToNextStep", "")
            print(text)
            if text == 'עבור_למקרר':
                status_new = 2
            if text == 'נאסף':
                status_new = 4
                # finished frige also means we need to reduce from inventory:
                remove_order_from_inventory(self.object)
            if text == 'נבדק':
                status_new = 6
            if text == 'הסתיים':
                status_new = 7
            if text == 'כלום':
                status_new = 7
            status_str_new = str(status_new)
            self.object.status = status_str_new
            print("in GoToNextStep - order status: ", self.object.status)
            self.object.save()
            set_status_time(self.object, status_str_new)

            return redirect_to_list(status_int_old)

        if 'GoToPrevStep' in request.POST:
            text = request.POST.get("GoToPrevStep", "")
            print(text)
            if text == 'חזור לכלום':
                status_new = 1
            if text == 'חזור לעוד לא הגיעו':
                status_new = 1
            if text == 'חזור להמתנה למקרר':
                status_new = 2
            if text == 'חזור להמתנה לבדיקה':
                status_new = 4
                # going back from this step means returning to frig,
                # so we also need to return the products to inventory:
                restore_order_to_inventory(self.object)
            if text == 'חזור להמתנה לתשלום':
                status_new = 6

            status_str_new = str(status_new)
            self.object.status = status_str_new
            print("in GoToPrevStep - order status: ", self.object.status)
            self.object.save()
            set_status_time(self.object, status_str_new)

            return redirect_to_list(status_int_old)

        if 'editOrder' in request.POST:
            this_order = self.get_object().id
            request.session['order_num'] = this_order
            if status_int_old > 3:  # ready to check or higher
                edit_inventory = True
            else:
                edit_inventory = False
            request.session['edit_inventory'] = edit_inventory
            return redirect('../editOrder/')

        if 'printOrder' in request.POST:
            this_order = self.get_object().id
            request.session['order_num'] = this_order
            return redirect('../ordersPrint/' + str(this_order))


class OrderPrintDetailView(DetailView):
    model = OrdersList
    template_name = "orders/order_for_printing.html"

    def  get_context_data(self, **kwargs):
        context = super(OrderPrintDetailView, self).get_context_data(**kwargs)
        context["customer"] = Customer.objects.get(id=self.object.customer_id.id)
        context["products_in_order"] = ProductOrderHelper.objects.filter(order_id=self.object.id).order_by('product_id__id')
        temp_objects = ProductOrderHelper.objects.filter(order_id=self.object.id)
        # .aggregate(total=Sum('progress', field="progress*estimated_days"))['total'])
        total = 0
        for obj in temp_objects:
            total = total+ obj.number_of_packages * obj.product_id.price

        # check if total is the same as total in ordersList
        # (this is temporary to make sure we can use total in ordersList)
        if total != self.object.total_price:
            print("!!!!!!!!!! total is different from total in orderslist: ", total, " vs ", self.object.total_price)


        context["total_price"] = total
        # action (according to status):
        self.object = self.get_object()  # change to this_object?
        status_int = int(self.object.status)
        print("order status: ", status_int)

        # if current status is 2 (waiting for frig)
        # we turn it to 3 (preparing in frig) while inside the order/
        # same for status 4 (ready to check) and 5 (checking)
        if status_int == 2:
            status_int = 3
        if status_int == 4:
            status_int = 5

        status_str_new = str(status_int)
        self.object.status = status_str_new

        self.object.save()

        context["action"] = ACTIONS_CHOICES[status_int]
        context["back_action"] = BACK_ACTIONS_CHOICES[status_int]
        context["comment"] = self.object.notes

        # set classes:
        context["confirmed_class"] = "notDone"
        context["here_to_take_class"] = "notDone"
        context["preparing_class"] = "notDone"
        context["ready_to_check_class"] = "notDone"
        context["checking_class"] = "notDone"
        context["ready_to_pay_class"] = "notDone"
        context["done_class"] = "notDone"
        if status_int > 1:
            context["confirmed_class"] = "done"
            if status_int > 2:
                context["here_to_take_class"] = "done"
                if status_int > 3:
                    context["preparing_class"] = "done"
                    if status_int > 4:
                        context["ready_to_check_class"] = "done"
                        if status_int > 5:
                            context["checking_class"] = "done"
                            if status_int > 6:
                                context["ready_to_pay_class"] = "done"
                                if status_int > 7:
                                    context["done_class"] = "done"

        # if self.object.take_on_friday:
        #     context["b_take_on_friday"] = True
        # else:
        #     context["b_take_on_friday"] = False
        if self.object.pre_prepared:
            context["b_pre_prepared"] = True
        else:
            context["b_pre_prepared"] = False
        if self.object.delivery_method == 3 | self.object.delivery_method == 4:
            context["delivery"] = True
        else:
            context["delivery"] = False
        if self.object.payed:
            context["b_payed"] = True
        else:
            context["b_payed"] = False
        # if self.object.for_second_holiday:
        #     context["b_second_holiday"] = True
        # else:
        #     context["b_second_holiday"] = False

        return context


class ListViewOrdersList(ListView):
    model = OrdersList
    template_name = "orders/orders_list.html"

    def get_context_data(self, **kwargs):
        context = super(ListViewOrdersList, self).get_context_data(**kwargs)
        context["list_title"] = get_title(self.kwargs['status'])
        context["all_deliveries_methods"] = all_deliveries_methods

        show_all = False
        if self.kwargs['status'] == 'all':
            show_all = True
            string_order_by = "foreign_order_id"
        elif self.kwargs['status'] == 'all_by_time':
            show_all = True
            string_order_by = "pick_up_time"
        elif self.kwargs['status'] == 'all_by_total_price':
            show_all = True
            string_order_by = "total_price"

        if show_all:
            all_orders_lists = []
            for i in range(len(all_deliveries_methods)):
                all_orders_lists_temp = OrdersList.objects.filter(delivery_method=i+1)\
                    .order_by(string_order_by) \
                    .values('id', 'foreign_order_id', 'customer_id__name', 'notes', 'pick_up_time', 'total_price', 'payed','customer_id__email','customer_id__address_city')
                all_orders_lists.append(all_orders_lists_temp)

        else:  # not show_all:
            status_int = self.kwargs['status']

            all_orders_lists = []
            for i in range(len(all_deliveries_methods)):
                temp_list = OrdersList.objects.filter(status=status_int, delivery_method=i + 1) \
                    .values('id', 'foreign_order_id', 'customer_id__name', 'notes', 'pick_up_time', 'total_price',
                            'payed', 'customer_id__email', 'customer_id__address_city')
                sorted_list = sort_by_status_time(temp_list, status_int)
                all_orders_lists.append(sorted_list)

        context["all_orders_lists"] = zip(all_orders_lists, all_deliveries_methods)

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
        context["list_title"] = 'סיכום המוצרים'
        # summing:
        all_products = Products.objects.all()
        all_orders_lines = ProductOrderHelper.objects.all()
        # all_orders_lines = ProductOrderHelper.objects.filter(order_id__take_on_friday=False)
        all_products_count_lines = ProductCounter.objects.all()

        print(all_orders_lines)

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
    if list_num == 1:
        return redirect('../list_confirmed/')
    if list_num == 2:
        return redirect('../list_here_to_take/')
    if list_num == 3:
        return redirect('../list_preparing_in_frig/')
    if list_num == 4:
        return redirect('../list_ready_to_check/')
    if list_num == 5:
        return redirect('../list_checking/')
    if list_num == 6:
        return redirect('../list_ready_to_pay/')
    if list_num == 7:
        return redirect('../list_done/')


def get_title(list_num):
    if list_num == '1':
        return 'orders confirmed'
    if list_num == '2':
        return 'orders waiting for fridge'
    if list_num == '3':
        return 'orders preparing in fridge'
    if list_num == '4':
        return 'orders ready to be checked'
    if list_num == '5':
        return 'orders checking'
    if list_num == '6':
        return 'orders ready to pay'
    if list_num == '7':
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
    if status_str == '1':
        return temp_list.order_by("id")
    if status_str == '2':
        return temp_list.order_by("here_to_take_time")
    if status_str == '3':
        return temp_list.order_by("here_to_take_time")
    if status_str == '4':
        return temp_list.order_by("ready_to_check_time")
    if status_str == '5':
        return temp_list.order_by("ready_to_check_time")
    if status_str == '6':
        return temp_list.order_by("ready_to_pay_time")
    if status_str == '7':
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
        return
    if status_str == '4':
        this_order.ready_to_check_time = time_now
        this_order.save()
        return
    if status_str == '5':
        return
    if status_str == '6':
        this_order.ready_to_pay_time = time_now
        this_order.save()
        return
    if status_str == '7':
        this_order.done_time = time_now
        this_order.save()
        return

