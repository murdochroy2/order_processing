from django.urls import path

from orders.views.order import OrderView
from orders.views.metrics import OrderMetricsView



urlpatterns = [
    path('orders/', OrderView.as_view(), name='orders-list'),
    path('orders/<str:order_id>', OrderView.as_view(), name='order-detail'),
    path('orders/metrics/', OrderMetricsView.as_view(), name='order-metrics'),
]