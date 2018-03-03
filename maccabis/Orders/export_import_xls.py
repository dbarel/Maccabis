from .models import ProductOrderHelper, OrdersList, Note, Products, ProductCounter, Customer
import xlwt, xlrd
import datetime
# from django.db.models import Sum, F
from xlrd import open_workbook


def import_orders(path):
    wb = open_workbook('C:\\Users\\dekel\\Desktop\\maccabis_django\\maccabis\\Orders\\ordersFiles\\orderDetails1.xlsx')
    for sheet in wb.sheets():
        number_of_rows = sheet.nrows
        # number_of_columns = sheet.ncols
        mail = []
        skip_order = 0
        order_num = 0
        this_item = 0
        for row in range(1, number_of_rows):
            print(" row: ", row)
            # check if this row starts a new order (email is changed):
            this_email = sheet.cell(row, 5).value
            if this_email != mail:
                mail = this_email
                # new order - check if already exists, if not - set a customer and fill order
                b_order_exists, order_num = check_if_customer_exists(this_email)
                if b_order_exists:
                    skip_order = 1
                else:
                    skip_order = 0
                    # new customer + new order started in 'check_if_customer_exists'.
                    # fill first item:
                    fill_item(order_num, this_item)
            else: # still same oder
                if skip_order:
                    continue
                else:
                    # fill another item:
                    fill_item(order_num, this_item)


def check_if_customer_exists(this_email):
    existing_customer = Customer.objects.filter(email=this_email)
    print("check for existing_customer: ", existing_customer)
    if existing_customer:
        # customer exists
        order_num = 0
        print("customer exists")
    else:  # no existing customer
        # add order to the list and give order number:
        # this_email = form.cleaned_data.get("email")
        this_customer = Customer.objects.get(email=this_email)
        print(this_customer, type(this_customer))

        this_order = OrdersList(customer_id=this_customer)
        this_order.save()

        # add order to all orders:
        order_num = this_order.id
        # store order number in the session:
        s_order_num = 'Customer added. Order number is:'
        s_order_num += str(order_num)
        print(s_order_num)

    return existing_customer, order_num

def fill_item(order_num, item):
    item=1

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

        existing_note = Note.objects.filter(order_id=order)
        if existing_note:
            comment = existing_note[0].comment
        else:
            comment = ''
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


