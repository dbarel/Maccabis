from django.conf.urls import url
from . import views
from django.views.generic import ListView
from .models import Customer
from .viewsLists2 import OrderDetailView,  ListViewOrdersList, ListViewProducts, ListViewCustomersList, OrderPrintDetailView

#ListViewHereToTake, ListViewToConfirm, ListViewConfirmed, ListViewReadyToCheck, ListViewReadyToPay, ListViewDone


urlpatterns = [
	url(r'^$', views.index),
	url(r'^manage/', views.manage),
	url(r'^customersView/', views.customers_view),
	url(r'^newOrder/(?P<pk>\d+)$', views.new_order),
	url(r'^newOrder/', views.new_order),
	url(r'^editOrder/', views.edit_order),
	url(r'^manageProducts/', ListViewProducts.as_view()),
	url(r'^manageProduct/(?P<pk>\d+)$', views.manage_product),
	url(r'^orders_list/', ListViewOrdersList.as_view(), {'status':'all'}),
	url(r'^orders_list_by_time/', ListViewOrdersList.as_view(), {'status':'all_by_time'}),
	url(r'^orders_list_by_total_price/', ListViewOrdersList.as_view(), {'status':'all_by_total_price'}),
	url(r'^orders/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Nothing'}),
	url(r'^ordersPrint/(?P<pk>\d+)$', OrderPrintDetailView.as_view(),{'action':'Nothing'}),
	url(r'^ordersToConfirm/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Confirmed'}),
	url(r'^ordersConfirmed/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'GoToFridge'}),
	url(r'^ordersHereToTake/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'FinishedFridge'}),
	url(r'^ordersReadyToCheck/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Checked'}),
	url(r'^ordersReadyToPay/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Done'}),
	url(r'^ordersDone/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'NoAction'}),
	url(r'^list_confirmed/', ListViewOrdersList.as_view(), {'status':'1'}),
	url(r'^list_here_to_take/', ListViewOrdersList.as_view(), {'status':'2'}),
	url(r'^list_preparing_in_frig/', ListViewOrdersList.as_view(), {'status':'3'}),
	url(r'^list_ready_to_check/', ListViewOrdersList.as_view(), {'status':'4'}),
	url(r'^list_checking/', ListViewOrdersList.as_view(), {'status':'5'}),
	url(r'^list_ready_to_pay/', ListViewOrdersList.as_view(), {'status':'6'}),
	url(r'^list_done/', ListViewOrdersList.as_view(), {'status':'7'}),
	url(r'^customers_list/', ListViewCustomersList.as_view( )),
]
