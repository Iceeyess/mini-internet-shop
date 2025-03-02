from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django import forms
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
    """Редактирование корзины. Добавил формсеты, чтобы была возможность удаления продукта из корзины, восстановления
    статуса False для is_for_preorder"""
    pre_order_formset = modelformset_factory(PreOrder, fields=['quantity'], extra=0, can_delete=True,
        widgets={'quantity': forms.NumberInput(attrs={'min': 1}, )
                 })
    if request.method == 'POST':
        formset = pre_order_formset(request.POST, queryset=PreOrder.objects.all())
        if formset.is_valid():
            instances = formset.save(commit=False)  # без commit=False не будет работать удаление

            for deleted_obj in formset.deleted_objects:
                item = deleted_obj.item
                if not PreOrder.objects.filter(item=item).exclude(pk=deleted_obj.pk).exists():
                    item.is_for_preorder = False
                    item.save()
                deleted_obj.delete()

            for instance in instances:
                instance.save()

            return redirect('trade:pre_order_detail')
    else:
        formset = pre_order_formset(queryset=PreOrder.objects.all())
    return render(request, template_name='trade/preorder_detail.html', context={'formset': formset})


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

