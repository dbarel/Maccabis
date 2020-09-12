import xlwt, xlrd
import datetime
from django.db.models import Sum, F
from xlrd import open_workbook
from .utils import add_order_line_to_helper
import glob
import os
from .models import ProductOrderHelper, OrdersList, Products, ProductCounter, Customer

all_deliveries_methods = ["איסוף עצמי ביום חמישי",
                          "איסוף עצמי ביום שישי",
                          "משלוח ביום חמישי",
                          "משלוח ביום שישי",
                          "משלוח מחוץ למודיעין"]


def export_meta_data(path):
    # path = 'C:\\Users\\dekel\\Orders\\'
    file_name = path + r'\meta_data.xls'

    book = xlwt.Workbook()
    sheet_name = 'all_orders'
    sh = book.add_sheet(sheet_name)
    # write your header first
    sh.write(0, 0, "הזמנה מספר")
    sh.write(0, 1, "שם הלקוח")
    sh.write(0, 2, "סכום הזמנה")
    sh.write(0, 3, "זמן הגעה")
    sh.write(0, 4, "הזמנה הגיעה לבדיקה")
    sh.write(0, 5, "הזמנה נבדקה")
    sh.write(0, 6, "הזמנה שולמה")

    n = 1
    for order in OrdersList.objects.all():
        sh.write(n, 0, order.id)
        sh.write(n, 1, order.customer_id.name)
        sh.write(n, 2, order.id)

        # comment = order.notes
        # sh.write(2, 0, "הערות")
        # sh.write(2, 1,  comment)
        sh.write(n, 3, str(order.here_to_take_time))
        sh.write(n, 4, str(order.ready_to_check_time))
        sh.write(n, 5, str(order.ready_to_pay_time))
        sh.write(n, 6, str(order.done_time))
        n = n + 1

    book.save(file_name)
    print('meadata saved')


def import_product_ids(full_path):
    wb = open_workbook(full_path)
    for sheet in wb.sheets():
        number_of_rows = sheet.nrows
        this_product = {'product_name': None, 'product_id_1': None,
                        'product_id_2': None}

        for row in range(1, number_of_rows):
            print(f'row:  {row} ')
            this_product['product_name'] = str(sheet.cell(row, 2).value)
            this_product['product_id_1'] = int(sheet.cell(row, 5).value)
            this_product['product_id_2'] = int(sheet.cell(row, 0).value)
            # Products.product_name
            # Products.foreign_product_id
            # Products.foreign_product_id_2
            # Products.price
            product = Products(product_name=str(sheet.cell(row, 2).value),
                               foreign_product_id=int(sheet.cell(row, 5).value),
                               foreign_product_id_2=int(sheet.cell(row, 0).value),
                               price=int(sheet.cell(row, 6).value)
                               )
            product.save()

            print(this_product)


def import_orders(path):
    # for all excel files in path:
    for filename in glob.glob(os.path.join(path, 'order_export*')):
        print(filename)

        wb = open_workbook(filename)
        for sheet in wb.sheets():
            number_of_rows = sheet.nrows
            this_order = {'order_num': None, 'name': None,
                          'last_name': None, 'phone': None,
                          'email': None, 'delivery_method_and_time': None, 'products': []}
            order_num_prev = ""
            for row in range(1, number_of_rows):
                print(" row: ", row)
                # check if this row starts a new order (header row):
                order_num = str(sheet.cell(row, 0).value)
                if order_num != order_num_prev:
                    order_num_prev = order_num
                    print("this row is new order")

                    # previous order is done - send it to ...
                    if this_order['order_num']:
                        print_order(this_order)
                        send_order_to_db(this_order)

                    print("starting new order")
                    # this line starts a new order
                    this_order['order_num'] = int(sheet.cell(row, 0).value)
                    this_order['name'] = str(sheet.cell(row, 3).value)
                    this_order['last_name'] = ""
                    this_order['phone'] = str(sheet.cell(row, 5).value)
                    # if sheet.cell(row, 4).value:
                    #     this_order['phone'] = "0{}".format(str(sheet.cell(row, 4).value)[:-2])
                    # elif sheet.cell(row, 3).value:
                    #     this_order['phone'] = "0{}".format(str(sheet.cell(row, 3).value)[:-2])
                    # else:
                    #     this_order['phone'] = ''
                    this_order['email'] = str(sheet.cell(row, 4).value)
                    this_order['address'] = str(sheet.cell(row, 13).value)
                    this_order['address_city'] = str(sheet.cell(row, 14).value)

                    this_order['notes'] = str(sheet.cell(row, 21).value)
                    this_order['payed'] = False
                    if str(sheet.cell(row, 8).value) == "שולם":
                        this_order['payed'] = True

                    this_order['delivery_method_and_time'] = str(sheet.cell(row, 12).value)

                    this_product = {'id': int(sheet.cell(row, 9).value),
                                    'product_name': str(sheet.cell(row, 7).value),
                                    'amount': int(sheet.cell(row, 18).value)}

                    this_order['products'].clear()
                    this_order['products'].append(this_product)

                else:
                    this_product = {'id': int(sheet.cell(row, 9).value),
                                    'product_name': str(sheet.cell(row, 7).value),
                                    'amount': int(sheet.cell(row, 18).value)}
                    this_order['products'].append(this_product)

            # last order is done - send it to ...
            print_order(this_order)
            send_order_to_db(this_order)


def send_order_to_db(extern_order):
    print('sending order ', extern_order['order_num'], 'to db')
    # check if order exists:
    existing_order = OrdersList.objects.filter(foreign_order_id=extern_order['order_num'])
    # if order exists - do nothing
    if existing_order:
        print('order exists. returning')
        return
    # if not - check if customer exists:
    # this_email = extern_order["email"]
    # existing_customer = Customer.objects.filter(email=this_email)
    this_name = extern_order['name'] + ' ' + extern_order['last_name']
    existing_customer = Customer.objects.filter(name=this_name)
    print("check for existing_customer: ", existing_customer)
    # if customer dose not exists - add customer
    if not existing_customer:
        print('add customer: ', extern_order['name'] + ' ' + extern_order['last_name'])
        this_customer = Customer(name=extern_order['name'] + ' ' + extern_order['last_name'],
                                 phone=extern_order['phone'],
                                 email=extern_order['email'],
                                 address=extern_order['address'],
                                 address_city=extern_order['address_city'])
        this_customer.save()
    else:
        print('customer exists!!!!!! adding order for same customer')
        this_customer = existing_customer.first()

    # parse delivery method and time:
    this_delivery_method = extern_order['delivery_method_and_time']
    for i in range(len(all_deliveries_methods)):
        if this_delivery_method.find(all_deliveries_methods[i]) == 0:
            delivery_method = i+1
            pick_up_time = datetime.datetime.now()
            break

    # add order:
    this_order = OrdersList(customer_id=this_customer, foreign_order_id=extern_order['order_num'],
                            notes=extern_order['notes'], pick_up_time=pick_up_time,
                            payed=extern_order['payed'], delivery_method=delivery_method)

    this_order.save()
    print('--order number ', this_order.id, 'added. number in website: ', extern_order['order_num'])
    print('pick up time for order is:', this_order.pick_up_time)

    # fill order:
    for p in extern_order['products']:
        product_name = p['product_name']
        product_foreign_id = p['id']
        quantity = p['amount']
        print(product_foreign_id, product_name)

        # was: if quantity > 0: # now we are checking for each product.
        # this is because if a product was changed from 1 to 0 we still need to make the change!!
        try:
            a = Products.objects.filter(foreign_product_id=product_foreign_id)
            print("this is a {}".format(a))
            this_product = Products.objects.get(foreign_product_id=product_foreign_id)

            print('success product_id')
        except Exception as e:
            print(e)
            this_product = Products.objects.get(foreign_product_id_2=product_foreign_id)
        edit_inventory = False
        add_order_line_to_helper(this_order, this_product, quantity, edit_inventory)

    # temp - for Rosh hashana 2020: add wine if total is >700
    if this_order.total_price >= 700:
        product_name = "יין אבשלום מתנה"
        product_foreign_id = 12346
        quantity = 1
        print(product_foreign_id, product_name + ' added as a gift')
        this_product = Products.objects.get(foreign_product_id=product_foreign_id)
        edit_inventory = False
        add_order_line_to_helper(this_order, this_product, quantity, edit_inventory)


def export_orders(path):
    # path = 'C:\\Users\\dekel\\Orders\\'
    file_name = path + 'allOrders.xls'

    book = xlwt.Workbook()

    for order in OrdersList.objects.all():
        order_id = order.id
        sheet_name = str(order_id) + ' ' + order.customer_id.name
        sh = book.add_sheet(sheet_name)
        # write your header first
        sh.write(0, 0, "הזמנה מספר")
        sh.write(0, 1, int(order_id))
        sh.write(1, 0, "שם הלקוח")
        sh.write(1, 1, order.customer_id.name)
        sh.write(1, 2, order.customer_id.email)
        sh.write(1, 3, order.customer_id.phone)

        comment = order.notes
        sh.write(2, 0, "הערות")
        sh.write(2, 1, comment)

        n = 4
        for order_line in ProductOrderHelper.objects.filter(order_id=order):
            sh.write(n, 0, order_line.product_id.product_name)
            sh.write(n, 1, int(order_line.number_of_packages))
            n = n + 1

    book.save(file_name)


def export_orders_list(path):
    # path = 'C:\\Users\\dekel\\Orders\\'
    file_name = os.path.join(path, 'allOrders_list.xls')
    print(file_name)
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yyyy'
    book = xlwt.Workbook()

    all_deliveries_methods_full = ["איסוף עצמי בחמישי 17.9 16-20",
                                      "איסוף עצמי בשישי 18.9 8-12",
                                      "משלוח בחמישי 17.9 16-20",
                                      "משלוח בשישי 18.9 8-12",
                                      "משלוח מחוץ למודיעין"]
    for this_delivery_method in range(1, 5):
        sh_1 = book.add_sheet(all_deliveries_methods_full[this_delivery_method])
        sh_1.write(0, 0, "הזמנה מספר")
        sh_1.write(0, 1, "שם הלקוח")
        sh_1.write(0, 2, "טלפון")
        sh_1.write(0, 6, "הערות")
        sh_1.write(0, 3, "סכום")
        sh_1.write(0, 4, "כתובת")
        sh_1.write(0, 5, "שולם")
        sh_1.write(0, 7, "שעת איסוף")
        i_pickup = 1
        for order in OrdersList.objects.filter(delivery_method=this_delivery_method):
            order_id = order.foreign_order_id
            sh_1.write(i_pickup, 0, int(order_id))
            sh_1.write(i_pickup, 1, order.customer_id.name)
            sh_1.write(i_pickup, 2, order.customer_id.phone)
            comment = order.notes
            sh_1.write(i_pickup, 6, comment)
            sh_1.write(i_pickup, 3, order.customer_id.email)
            sh_1.write(i_pickup, 4, order.customer_id.address + ' ' + order.customer_id.address_city)
            if order.payed:
                sh_1.write(i_pickup, 5, "שולם")
            sh_1.write(i_pickup, 7, str(order.pick_up_time))

            i_pickup = i_pickup+1

    book.save(file_name)


def export_inventory(path):
    # path = 'C:\\Users\\dekel\\Orders\\'
    file_name_temp = 'inventory_' + str(datetime.datetime.now().strftime("%Y_%m_%d %H_%M_%S")) + '.xls'

    file_name = os.path.join(path, file_name_temp)

    # print(file_name)

    book = xlwt.Workbook()
    sh = book.add_sheet("סיכומים")
    # write your header first
    sh.write(0, 0, "מוצר")
    sh.write(0, 1, "כמות אריזות שהוזמנה")
    sh.write(0, 2, "כמות אריזות שהוכנה")
    sh.write(0, 3, "כמות אריזות אי זוגי")
    sh.write(0, 4, "מחיר")

    all_products = Products.objects.all()
    all_orders_lines = ProductOrderHelper.objects.all()
    all_products_count_lines = ProductCounter.objects.all()

    n = 1
    for product in all_products:
        # ordered:
        temp = all_orders_lines.filter(product_id=product).aggregate(Sum('number_of_packages'))
        num_of_odd_packages = all_orders_lines.annotate(odd=F('number_of_packages') % 2). \
            filter(product_id=product, odd=True).count()
        val_ordered = temp['number_of_packages__sum']
        val_ordered = int(0 if val_ordered is None else val_ordered)
        # sum_ordered.append(val_ordered)

        # prepared:
        temp = all_products_count_lines.filter(product_id=product, action='p').aggregate(Sum('number_of_packages'))
        val_prepared = temp['number_of_packages__sum']
        val_prepared = int(0 if val_prepared is None else val_prepared)
        # sum_prepared.append(val_prepared)

        sh.write(n, 0, product.product_name)
        sh.write(n, 1, val_ordered)
        sh.write(n, 2, val_prepared)
        sh.write(n, 3, num_of_odd_packages)
        sh.write(n, 4, product.price)
        n = n + 1

    book.save(file_name)
    print(file_name)


def print_order(order):
    print(order['order_num'])
    print(order['name'])
    print(order['last_name'])
    print(order['phone'])
    print(order['email'])
    for p in order['products']:
        print(p['id'], p['product_name'], p['amount'])


# main is not working
#  if __name__ == '__main__':
#     # import_orders(r'C:\Users\dekel\Desktop\maccabis_django\fromWebsite_RoshHashana2019')
#     import_product_ids(r'C:\Users\dekel\Desktop\maccabis_django\ids\both.xls')
