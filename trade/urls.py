from trade.apps import TradeConfig
from django.urls import path

from trade.views import ItemDetailView, ItemListView, payment_session, create_pre_order, pre_order_detail

app_name = TradeConfig.name

urlpatterns = [
    path('', ItemListView.as_view(), name='trade_list'),
    path('item/<int:pk>/', ItemDetailView.as_view(), name='trade_detail'),
    path('mark_for_trade/<int:pk>/', create_pre_order, name='mark_for_trade'),  # Метод для пометки товара для покупки

    path('buy/<int:pk>/', payment_session, name='create_payment_session'),
    path('pre_order/', pre_order_detail, name='order_detail'),
]
