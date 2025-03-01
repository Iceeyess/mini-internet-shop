from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, CreateView

from config.settings import STRIPE_SECRET_KEY
from trade.models import Item, Order, PreOrder, Currency
import stripe

# Create your views here.


class ItemListView(ListView):
    """Класс списка товара"""
    model = Item


class ItemDetailView(DetailView):
    """Класс детализации товара"""
    model = Item


def create_pre_order(request, pk):
    """Метод для пометки товара для покупки. Создание корзины(предзаказ).
    Хеширование товаров (не через IP, пока).
    1. Если товара еще нет в корзине, то он создается с определенным номером хеша.
    2. Если корзина уже что-то имеет, то проверяется есть ли товар там или нет. Если товара нет, то создается доп. линия
    с тем же хэшем, а если товар есть, то в объекте (item) убирается пометка для корзины is_for_preorder становится
    False"""
    quantity = request.GET.get('quantity', 1)
    obj = get_object_or_404(Item, pk=pk)
    pre_order = PreOrder.objects.all()
    if not pre_order.exists():
        PreOrder.objects.create(item=obj, quantity=quantity)
        obj.is_for_preorder = True
        obj.quantity = quantity

    elif pre_order.exists() and obj in [_.item for _ in pre_order]:
        obj.is_for_preorder = False
        pre_order.filter(item=obj).delete()

    elif pre_order.exists() and not obj in [_.item for _ in pre_order]:
        obj.is_for_preorder = True
        session_tag = PreOrder.objects.all().last().session_tag  # копируем уже созданный тег и прикрепляем
        new_preorder = PreOrder.objects.create(item=obj, quantity=quantity)
        new_preorder.session_tag = session_tag
        obj.quantity = quantity
        new_preorder.save()
    obj.save()
    return redirect(reverse('trade:trade_detail', kwargs={'pk': obj.pk}))


def pre_order_detail(request):
    pre_order_list = PreOrder.objects.all()
    return render(request, template_name='trade/preorder_detail.html', context={'pre_order_list': pre_order_list})

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

