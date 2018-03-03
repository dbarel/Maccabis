from django.conf.urls import url
from . import views
from django.views.generic import ListView
from .models import Customer
from .viewsLists2 import OrderDetailView,  ListViewOrdersList, ListViewProducts, ListViewCustomersList

#ListViewHereToTake, ListViewToConfirm, ListViewConfirmed, ListViewReadyToCheck, ListViewReadyToPay, ListViewDone


urlpatterns = [
	url(r'^$', views.index),
	url(r'^manage/', views.manage),
	url(r'^newOrder/(?P<pk>\d+)$', views.new_order),
	url(r'^newOrder/', views.new_order),
	url(r'^editOrder/', views.edit_order),
	url(r'^manageProducts/', ListViewProducts.as_view()),
	url(r'^manageProduct/(?P<pk>\d+)$', views.manage_product),
	url(r'^orders_list/', ListViewOrdersList.as_view(), {'status':'all'}),
	url(r'^orders/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Nothing'}),
	url(r'^ordersToConfirm/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Confirm'}),
	url(r'^ordersConfirmed/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'GoToFridge'}),
	url(r'^ordersHereToTake/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'FinishedFridge'}),
	url(r'^ordersReadyToCheck/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Checked'}),
	url(r'^ordersReadyToPay/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'Done'}),
	url(r'^ordersDone/(?P<pk>\d+)$', OrderDetailView.as_view(),{'action':'NoAction'}),
	url(r'^list_to_confirm/', ListViewOrdersList.as_view(), {'status':'0'}),
	url(r'^list_confirmed/', ListViewOrdersList.as_view(), {'status':'1'}),
	url(r'^list_here_to_take/', ListViewOrdersList.as_view(), {'status':'2'}),
	url(r'^list_ready_to_check/', ListViewOrdersList.as_view(), {'status':'3'}),
	url(r'^list_ready_to_pay/', ListViewOrdersList.as_view(), {'status':'4'}),
	url(r'^list_done/', ListViewOrdersList.as_view(), {'status':'5'}),
	url(r'^customers_list/', ListViewCustomersList.as_view( )),
]
