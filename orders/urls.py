from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),

    path('process-payment/', views.process_payment, name='process_payment'),
    path('order_complete/', views.order_complete, name='order_complete'),

    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),

]
