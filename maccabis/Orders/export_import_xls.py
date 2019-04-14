from .models import ProductOrderHelper, OrdersList, Products, ProductCounter, Customer
import xlwt, xlrd
import datetime
from django.db.models import Sum, F
from xlrd import open_workbook
from .utils import add_order_line_to_helper
import glob
import os


def export_meta_data(path):

    # path = 'C:\\Users\\dekel\\Orders\\'
    file_name = path + 'meta_data.xls'

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

    n=1
    for order in OrdersList.objects.all():
        sh.write(n, 0,  order.id)
        sh.write(n, 1,  order.customer_id.name)
        sh.write(n, 2,  order.id)

        # comment = order.notes
        # sh.write(2, 0, "הערות")
        # sh.write(2, 1,  comment)
        sh.write(n, 3,  str(order.here_to_take_time))
        sh.write(n, 4,  str(order.ready_to_check_time))
        sh.write(n, 5,  str(order.ready_to_pay_time))
        sh.write(n, 6,  str(order.done_time))
        n = n+1

    book.save(file_name)


def import_orders(path):
    # for all excel files in path:
    for filename in glob.glob(os.path.join(path, 'orderDetails_*')):
        print(filename)

        wb = open_workbook(filename)
        for sheet in wb.sheets():
            number_of_rows = sheet.nrows
            this_order = {'order_num': None, 'name': None,
                          'last_name': None, 'phone': None,
                          'email': None, 'products': []}
            next_row_is_new_order = False
            for row in range(0, number_of_rows):
                print(" row: ", row)
                # check if this row starts a new order (header row):
                order_num = str(sheet.cell(row, 0).value)
                if order_num == "מספר הזמנה":
                    print("nex row is new order")
                    next_row_is_new_order = True

                    # previous order is done - send it to ...
                    if this_order['order_num']:
                        print_order(this_order)
                        send_order_to_db(this_order)
                    continue

                if next_row_is_new_order:
                    print("next_row_is_new_order")
                    # this line starts a new order
                    next_row_is_new_order = False
                    this_order['order_num'] = int(sheet.cell(row, 0).value)
                    this_order['name'] = str(sheet.cell(row, 1).value)
                    this_order['last_name'] = str(sheet.cell(row, 2).value)
                    if sheet.cell(row, 4).value:
                        this_order['phone'] = str(sheet.cell(row, 4).value)
                    elif sheet.cell(row, 3).value:
                        this_order['phone'] = str(sheet.cell(row, 3).value)
                    else:
                        this_order['phone'] = ''
                    this_order['email'] = str(sheet.cell(row, 5).value)
                    this_order['notes'] = str(sheet.cell(row, 10).value)
                    this_product = {'id': int(sheet.cell(row, 11).value), 'product_name': str(sheet.cell(row, 12).value),
                                    'amount': int(sheet.cell(row, 15).value)}
                    this_order['products'].clear()
                    this_order['products'].append(this_product)
                else:
                    this_product = {'id': int(sheet.cell(row, 11).value), 'product_name': str(sheet.cell(row, 12).value),
                                    'amount': int(sheet.cell(row, 15).value)}
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
    this_name = extern_order['name']+' '+extern_order['last_name']
    existing_customer = Customer.objects.filter(name=this_name)
    print("check for existing_customer: ", existing_customer)
    # if customer dose not exists - add customer
    if not existing_customer:
        print('add customer: ', extern_order['name']+' '+extern_order['last_name'])
        this_customer = Customer(name=extern_order['name']+' '+extern_order['last_name'], phone=extern_order['phone'],
                                 email=extern_order['email'])
        this_customer.save()
    else:
        print('customer exists!!!!!! adding order for same customer')
        this_customer = existing_customer.first()

    # add order:
    this_order = OrdersList(customer_id=this_customer, foreign_order_id=extern_order['order_num'],
                            notes=extern_order['notes'])
    this_order.save()
    print('--order number ', this_order.id, 'added. number in website: ', extern_order['order_num'])

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
            print ("this is a {}".format(a))
            this_product = Products.objects.get(foreign_product_id=product_foreign_id)

            print('success product_id')
        except Exception as e:
            print(e)
            this_product = Products.objects.get(foreign_product_id_2=product_foreign_id)
        edit_inventory = False
        add_order_line_to_helper(this_order, this_product, quantity, edit_inventory)


def export_orders(path):

    # path = 'C:\\Users\\dekel\\Orders\\'
    file_name = path + 'allOrders.xls'

    book = xlwt.Workbook()

    for order in OrdersList.objects.all():
        order_id = order.id
        sheet_name = str(order_id)+' '+order.customer_id.name
        sh = book.add_sheet(sheet_name)
        # write your header first
        sh.write(0, 0, "הזמנה מספר")
        sh.write(0, 1, int(order_id))
        sh.write(1, 0, "שם הלקוח")
        sh.write(1, 1,  order.customer_id.name)
        sh.write(1, 2,  order.customer_id.email)
        sh.write(1, 3,  order.customer_id.phone)

        comment = order.notes
        sh.write(2, 0, "הערות")
        sh.write(2, 1,  comment)

        n = 4
        for order_line in ProductOrderHelper.objects.filter(order_id=order):
            sh.write(n, 0, order_line.product_id.product_name)
            sh.write(n, 1, int(order_line.number_of_packages))
            n = n+1

    book.save(file_name)


def export_inventory(path):
    # path = 'C:\\Users\\dekel\\Orders\\'
    file_name = path+'inventory_'+str(datetime.datetime.now().strftime("%Y_%m_%d %H_%M_%S"))+'.xls'
    # print(file_name)

    book = xlwt.Workbook()
    sh = book.add_sheet("סיכומים")
    # write your header first
    sh.write(0, 0, "מוצר")
    sh.write(0, 1, "כמות אריזות שהוזמנה")
    sh.write(0, 2, "כמות אריזות שהוכנה")
    sh.write(0, 3, "כמות אריזות אי זוגי")

    all_products = Products.objects.all()
    all_orders_lines = ProductOrderHelper.objects.all()
    all_products_count_lines = ProductCounter.objects.all()

    n = 1
    for product in all_products:
        # ordered:
        temp = all_orders_lines.filter(product_id=product).aggregate(Sum('number_of_packages'))
        num_of_odd_packages = all_orders_lines.annotate(odd=F('number_of_packages') % 2).\
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
        n = n+1

    book.save(file_name)


def print_order(order):
    print(order['order_num'])
    print(order['name'])
    print(order['last_name'])
    print(order['phone'])
    print(order['email'])
    for p in order['products']:
        print(p['id'], p['product_name'], p['amount'])


if __name__ == '__main__':
    import_orders(r'C:\Users\dekel\Desktop\maccabis_django\fromWebsite_Pesah2019')