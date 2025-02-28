from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, CreateView

from config.settings import STRIPE_SECRET_KEY
from trade.models import Item, Order, PreOrder
import stripe

# Create your views here.


class ItemListView(ListView):
    """Класс списка товара"""
    model = Item


class ItemDetailView(DetailView):
    """Класс детализации товара"""
    model = Item


def create_pre_order(request, pk, quantity):
    """Метод для пометки товара для покупки"""
    obj = get_object_or_404(Item, pk=pk)
    pre_order = PreOrder.objects.all()
    if not pre_order.exists():
        PreOrder.objects.create()
        obj.is_for_transaction = True
        obj.quantity = quantity
    elif pre_order.exists() and obj.item in [_.item for _ in pre_order]:
        obj.is_for_transaction = False
        pre_order.filter(item=obj).delete()
    else:
        obj.is_for_transaction = True
        obj.quantity = quantity
        obj.hash_tag = PreOrder.objects.all()[0].hash_tag
    obj.save(), pre_order.save()
    return redirect(reverse('trade:trade_detail', kwargs={'pk': obj.pk}))


def payment_session(request, pk):
    """Метод для получения сессии оплаты"""
    obj = Item.objects.get(pk=pk)
    stripe.api_key = STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        line_items=[{
            'price_data': {
                'currency': 'rub',
                'product_data': {
                    'name': obj.name,
                },
                'unit_amount': int(obj.price),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f'{request._current_scheme_host + reverse("trade:trade_list")}',
        cancel_url=f'{request._current_scheme_host + reverse("trade:trade_list")}',
    )
    return redirect(session.url)


class OrderCreateView(CreateView):
    """Класс создания заказа (корзина)"""
    model = Order
    fields = ['item', 'quantity', 'tax', 'discount']
