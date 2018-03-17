from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from .forms import FormCustomer, FormProductCounter, FormNote
from .models import Products, TempOrder, OrdersList, Customer, ProductCounter, ProductOrderHelper
from .utils import add_order_line_to_helper
from .export_import_xls import export_orders, export_inventory, import_orders
import datetime
# import pdb


def index(request):
    return render(request, 'orders/home.html')


def manage(request):
    print('importing...')
    import_orders('C:\\Users\\dekel\\Desktop\\maccabis_django\\maccabis\\Orders\\ordersFiles\\2018_03_16_a.xlsx')

    print('exporting all...')
    path = 'C:\\Users\\dekel\\Orders\\'
    export_orders(path)
    export_inventory(path)
    context = {
        "str_orders": "orders exported to: " + path,
        "str_inventory": "inventory exported to: " + path,
    }

    return render(request, 'orders/exported.html', context)


def orders_export_all(request):
    path = 'C:\\Users\\dekel\\Orders\\'
    export_orders(path)
    export_inventory(path)
    context = {
        "str_orders": "orders exported to: " + path,
    }
    return render(request, 'orders/exported.html', context)


def inventory_export(request):
    path = 'C:\\Users\\dekel\\Orders\\'
    export_inventory(path)
    context = {
        "str_inventory": "inventory exported to: "+path,
    }
    return render(request, 'orders/exported.html', context)


def manage_product(request, pk):
    print("beginning of manage_product")
    form = FormProductCounter(request.POST or None)
    this_product = Products.objects.get(id=pk)
    product_name = this_product.product_name
    context = {
        "form": form,
        "product_name": product_name,
    }
    if request.POST:
        if form.is_valid():
            # update model:
            print("product form is valid", type(form))
            # instance = form.save(commit=False)
            # instance.save()

            # add order to the list and give order number:
            number_of_packs = form.cleaned_data.get("number_of_packages")
            owner = form.cleaned_data.get("owner")
            action = form.cleaned_data.get("action")

            this_product = Products.objects.get(id=pk)
            this_line = ProductCounter(product_id=this_product, number_of_packages=number_of_packs, owner=owner, action=action)
            this_line.time = datetime.datetime.now()
            this_line.save()
            print("productCounter new line: ", this_product, number_of_packs, action, owner)

            return redirect('../manageProducts/')

        else:
            print("problem with form product counter - try again")
    return render(request, 'orders/manage_product.html', context)


def new_order(request, pk=None):
    print("beginning of new_order. customer_id = ", pk)

    if pk:
        init_customer = Customer.objects.get(pk=pk)
        init_data = {'name':init_customer.name, 'phone':init_customer.phone, 'email':init_customer.email}
        form = FormCustomer(request.POST or None, initial=init_data)
    else:
        form = FormCustomer(request.POST or None)
    s_order_num = 'to get an order number, you need to add/choose a customer'

    form_note = FormNote(request.POST or None)

    if request.POST:

        formset_product = modelformset_factory(TempOrder, fields=('product_name', 'price', 'number_of_packs'), extra=0)
        formset = formset_product(request.POST or None, queryset=TempOrder.objects.all(), )

        print('returned from this page (post)')
        if '_addCustomer' in request.POST:
            print("in _addCustomer")
            if form.is_valid():

                # make sure this customer doesn't already exist:
                this_email = form.cleaned_data.get("email")
                existing_customer = Customer.objects.filter(email=this_email)
                print("check for existing_customer: ", existing_customer)
                if existing_customer:
                    print("customer already exists, need to use the other button")
                    s_order_num = 'customer already exists, please use button for: Get order for existing customer'
                    context = {
                        "form1": form,
                        "formset1": formset,
                        "s_order_num": s_order_num,
                    }
                    return render(request, 'orders/newOrder.html', context)
                else:  # no existing customer
                    instance = form.save(commit=False)
                    instance.save()
                    print(form.cleaned_data.get("name"))

                    # add order to the list and give order number:
                    # this_email = form.cleaned_data.get("email")
                    this_customer = Customer.objects.get(email=this_email)
                    print(this_customer, type(this_customer))

                    this_order = OrdersList(customer_id=this_customer)
                    this_order.save()

                    # add order to all orders:
                    # list_item_to_confirm = ListOrdersToConfirm(order_id=this_order)
                    # list_item_to_confirm.save()

                    order_num = this_order.id
                    # store order number in the session:
                    request.session['order_num'] = order_num
                    s_order_num = 'Customer added. Order number is:'
                    s_order_num += str(order_num)

                    context = {
                        "form1": form,
                        "formset1": formset,
                        "s_order_num": s_order_num,
                        "form_note": form_note,
                    }
                    return render(request, 'orders/newOrder.html', context)
            else:  # form.is_valid():
                context = {
                    "form1": form,
                    "formset1": formset,
                    "s_order_num": s_order_num,
                    "form_note": form_note,
                }
                return render(request, 'orders/newOrder.html', context)

        elif '_useExistingCustomer' in request.POST:
            if form.is_valid():
                this_email = form.cleaned_data.get("email")
                existing_customer = Customer.objects.filter(email=this_email)

                if not existing_customer:
                    s_order_num = 'no customer with this name found. please add this customer'

                    context = {
                        "form1": form,
                        "formset1": formset,
                        "s_order_num": s_order_num,
                        "form_note": form_note,
                    }
                    return render(request, 'orders/newOrder.html', context)
                else:
                    this_customer = existing_customer.first()
                    this_order = OrdersList(customer_id=this_customer)
                    this_order.save()

                    order_num = this_order.id
                    # store order number in the session:
                    request.session['order_num'] = order_num
                    s_order_num = 'Existing customer used. Order number is:'
                    s_order_num += str(order_num)

                    context = {
                        "form1": form,
                        "formset1": formset,
                        "s_order_num": s_order_num,
                        "form_note": form_note,
                    }
                    return render(request, 'orders/newOrder.html', context)
            else:  # form.is_valid():
                context = {
                    "form1": form,
                    "formset1": formset,
                    "s_order_num": s_order_num,
                    "form_note": form_note,
                }
                return render(request, 'orders/newOrder.html', context)

        elif '_addOrder' in request.POST:
            print("in add order")
            if formset.is_valid():
                print("in _addOrder. formset valid")

                # add order details:
                order_num = request.session['order_num']
                print(order_num)
                this_order = OrdersList.objects.get(id=order_num)
                print("this order:", this_order)
                print("this_order.id:", this_order.id)

                # add order details:
                for f in formset:
                    cd = f.cleaned_data
                    product_name = cd.get('product_name')
                    quantity = cd.get('number_of_packs')

                    # was: if quantity > 0: # now we are checking for each product.
                    # this is because if a product was changed from 1 to 0 we still need to make the change!!
                    this_product = Products.objects.get(product_name=product_name)
                    edit_inventory = False
                    add_order_line_to_helper(this_order, this_product, quantity, edit_inventory)

                # comment:
                if form_note.data['notes']:
                    this_order.notes = form_note.data['notes']
                    this_order.save()
                    print("note added")

                request.session['order_num'] = order_num
                s_order_num = 'You can still edit order '
                s_order_num += str(order_num)
                s_order_num += '. For a new order, add/choose a different customer'

                context = {
                    "form1": form,
                    "formset1": formset,
                    "s_order_num": s_order_num,
                    "form_note": form_note,
                }
                return render(request, 'orders/newOrder.html', context)

            else:   # formset.is_valid():
                print("in _addOrder. formset not valid")
                s_order_num = 'There was a problem with this order, try to start again'
                context = {
                    "form1": form,
                    "formset1": formset,
                    "s_order_num": s_order_num,
                    "form_note": form_note,
                }
                return render(request, 'orders/newOrder.html', context)
    else:   # got here from a different page
        print("i'm not in request post")

        # new temp order:
        TempOrder.objects.all().delete()
        products_list = Products.objects.all()
        for item in products_list:
            this_name = item.product_name
            this_price = item.price
            to = TempOrder(product_name=this_name, price=this_price, number_of_packs=0)
            to.save()

        formset_product = modelformset_factory(TempOrder, fields=('product_name', 'price', 'number_of_packs'), extra=0)
        formset = formset_product(request.POST or None, queryset=TempOrder.objects.all(), )

        # render:
        context = {
            "form1": form,
            "formset1": formset,
            "s_order_num": s_order_num,
            "form_note": form_note,
            }

        return render(request, 'orders/newOrder.html', context)


def edit_order(request):
    if not request.POST:
        this_order_id = request.session.get('order_num')
        # edit_inventory = request.session.get('edit_inventory')
        s_edit_order = "edit order number: " + str(this_order_id)
        print("edit order number: ", this_order_id)
        all_items_this_order = ProductOrderHelper.objects.filter(order_id=this_order_id)

        # new temp order:
        TempOrder.objects.all().delete()
        products_list = Products.objects.all()
        for item in products_list:
            this_name = item.product_name
            this_price = item.price
            this_item = all_items_this_order.filter(product_id=item).first()
            if not this_item:
                to = TempOrder(product_name=this_name, price=this_price, number_of_packs=0)
            else:
                to = TempOrder(product_name=this_name, price=this_price, number_of_packs=this_item.number_of_packages)
            to.save()

        formset_product = modelformset_factory(TempOrder, fields=('product_name', 'price', 'number_of_packs'), extra=0)
        formset = formset_product(request.POST or None, queryset=TempOrder.objects.all(), )

        this_order = OrdersList.objects.get(id=this_order_id)
        existing_note = this_order.notes
        if existing_note:
            print(existing_note)
            init_data = {'notes': str(existing_note), 'take_on_friday': this_order.take_on_friday,
                         'delivery': this_order.delivery, 'for_second_holiday': this_order.for_second_holiday}
            form_note = FormNote(request.POST or None, initial=init_data)
        else:
            init_data = {'take_on_friday': this_order.take_on_friday,
                         'delivery': this_order.delivery, 'for_second_holiday': this_order.for_second_holiday}
            form_note = FormNote(request.POST or None, initial=init_data)

        # render:
        context = {
            "formset1": formset,
            "s_order_num": s_edit_order,
            "form_note": form_note,
        }

        return render(request, 'orders/editOrder.html', context)

    else:  # request in post
        order_num = request.session.get('order_num')
        edit_inventory = request.session.get('edit_inventory')
        formset_product = modelformset_factory(TempOrder, fields=('product_name', 'price', 'number_of_packs'), extra=0)
        formset = formset_product(request.POST or None, queryset=TempOrder.objects.all(), )
        form_note = FormNote(request.POST or None)

        # update order:
        if formset.is_valid():
            # add order details:
            print(order_num)
            this_order = OrdersList.objects.get(id=order_num)
            print("this order:", this_order)
            print("this_order.id:", this_order.id)

            # add order details:
            for f in formset:
                cd = f.cleaned_data
                product_name = cd.get('product_name')
                quantity = cd.get('number_of_packs')

                # print(product_name, quantity)
                this_product = Products.objects.get(product_name=product_name)
                add_order_line_to_helper(this_order, this_product, quantity, edit_inventory)

            # comment:
            if form_note.is_valid():
                this_order = OrdersList.objects.get(id=order_num)
                existing_note = this_order.notes
                if form_note.data['notes']:
                    if existing_note:
                        this_order.notes = form_note.data['notes']
                        this_order.save()
                    else:
                        this_order.notes = form_note.data['notes']
                        this_order.save()
                        print("note added")
                else:
                    if existing_note:
                        this_order.notes = ''
                        this_order.save()

                # update boolean fields:
                # print(form_note.cleaned_data, type(form_note.cleaned_data))
                this_order.take_on_friday = form_note.cleaned_data.get('take_on_friday')
                this_order.delivery = form_note.cleaned_data.get('delivery')
                this_order.for_second_holiday = form_note.cleaned_data.get('for_second_holiday')
                this_order.save()

        return redirect('../orders/'+str(order_num))



