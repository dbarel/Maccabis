import datetime
from .models import ProductOrderHelper, ProductCounter


def add_order_line_to_helper(this_order, this_product, quantity, edit_inventory):
    # first check if a line with this order number and this product exists:
    all_lines_from_this_order = ProductOrderHelper.objects.filter(order_id=this_order, product_id=this_product)

    print("product: ", this_product, all_lines_from_this_order, "quantity = ", quantity)
    if (not all_lines_from_this_order) and (quantity > 0):
        # if it doesn't - add it:
        order_line = ProductOrderHelper(order_id=this_order, product_id=this_product, number_of_packages=quantity)
        order_line.save()
        print("line added! line num:", order_line.id, "order num: ", order_line.order_id, "prod:",
              order_line.product_id, order_line.number_of_packages, "datetime: ", order_line.time)
        # according to status, we might need to remove these items from inventory:
        if edit_inventory:
            quantity_diff = quantity
            # remove quantity_diff from storage:
            owner_str = "add_order_id_" + str(this_order)
            new_line = ProductCounter(product_id=this_product, number_of_packages=quantity_diff,
                                      time=datetime.datetime.now(), action='to', owner=owner_str)
            print("editing inventory  product ", this_product, ", ", quantity_diff, " packs, ",
                  owner_str)
            new_line.save()
    elif all_lines_from_this_order.count() == 1:
        # if it does - amend it, but add to changes the details of the previous value:
        old_quantity = all_lines_from_this_order[0].number_of_packages
        if old_quantity == quantity:
            return
        old_time = all_lines_from_this_order[0].time
        new_time = datetime.datetime.now()
        all_lines_from_this_order[0].number_of_packages = quantity
        all_lines_from_this_order[0].time = new_time
        all_lines_from_this_order[0].changes = \
            all_lines_from_this_order[0].changes + old_time.strftime('%Y/%m/%d %H:%M:%S') + " quantity was:" + str(old_quantity) + " * "
        all_lines_from_this_order[0].save()
        print("line changed! line num: ", all_lines_from_this_order[0].id, "order num: ",
              all_lines_from_this_order[0].order_id,
              "prod:", all_lines_from_this_order[0].product_id,
              "packages: ", all_lines_from_this_order[0].number_of_packages,
              "datetime: ", all_lines_from_this_order[0].time,
              "changes: ", all_lines_from_this_order[0].changes)
        if edit_inventory:
            quantity_diff = quantity - old_quantity
            if quantity_diff > 0:
                # remove quantity_diff from storage
                owner_str = "add_order_id_" + str(this_order)
                action_str = 'to'
            else:
                # add quantity_diff from storage
                owner_str = "return_order_id_" + str(this_order)
                quantity_diff = abs(quantity_diff)
                action_str = 'ro'
        new_line = ProductCounter(product_id=all_lines_from_this_order[0].product_id,number_of_packages=quantity_diff,
                                  time=datetime.datetime.now(), action=action_str, owner=owner_str)
        print("editing inventory product ", all_lines_from_this_order[0].product_id, ", ", quantity_diff, " packs, ",
              owner_str)
        new_line.save()

    elif all_lines_from_this_order.count() > 1:
        # error - this line has more than one occurrence:
        print("Error! more than one occurrence for order ", all_lines_from_this_order[0].order_id,
              "prod:", all_lines_from_this_order[0].product_id)
    else:
        return


# def check_if_need_to_be_zeroed(this_order, this_product, quantity):
#     # first check if a line with this order number and this product exists:
#     all_lines_from_this_order = ProductOrderHelper.objects.filter(order_id=this_order, product_id=this_product)
#     print("eti1 ")
#     print(this_product)
#     print(all_lines_from_this_order)
#     if all_lines_from_this_order.count() == 1:
#         print("eti2 ")
#         old_quantity = all_lines_from_this_order[0].number_of_packages
#
#         old_time = all_lines_from_this_order[0].time
#         new_time = datetime.datetime.now()
#         all_lines_from_this_order[0].number_of_packages = quantity
#         print(all_lines_from_this_order[0].number_of_packages)
#         all_lines_from_this_order[0].time = new_time
#         all_lines_from_this_order[0].changes = \
#             all_lines_from_this_order[0].changes + old_time.strftime('%Y/%m/%d %H:%M:%S') + " quantity was:" + str(
#                 old_quantity) + " * "
#         print(all_lines_from_this_order[0].number_of_packages)
#         all_lines_from_this_order[0].save()
#         print(all_lines_from_this_order[0].number_of_packages)
#         print("line changed! line num: ", all_lines_from_this_order[0].id, "order num: ",
#               all_lines_from_this_order[0].order_id,
#               "prod:", all_lines_from_this_order[0].product_id,
#               "packages: ", all_lines_from_this_order[0].number_of_packages,
#               "datetime: ", all_lines_from_this_order[0].time,
#               "changes: ", all_lines_from_this_order[0].changes)
#     else:
#         return
