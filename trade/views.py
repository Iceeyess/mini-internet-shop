from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django import forms
from django.views.generic import DetailView, ListView, CreateView
from ipware import get_client_ip

from config.settings import STRIPE_SECRET_KEY
from trade.models import Item, Order, PreOrder, Currency, Tax
import stripe


# Create your views here.


class ItemListView(ListView):
    """Класс списка товара"""
    model = Item


class ItemDetailView(DetailView):
    """Класс детализации товара"""
    model = Item
    extra_context = {'tax': Tax.objects.filter(name='НДС')[0]}


def create_pre_order(request, pk):
    """Метод для пометки товара для покупки. Создание корзины(предзаказ).
    """
    quantity = request.GET.get('quantity', 1)
    obj = get_object_or_404(Item, pk=pk)
    client_ip, _ = get_client_ip(request)  # IP address
    preorder_by_ip = PreOrder.objects.filter(client_ip=client_ip)
    if not preorder_by_ip.exists():
        PreOrder.objects.create(item=obj, quantity=quantity, client_ip=client_ip)
        obj.is_for_preorder = True
        obj.quantity = quantity

    elif preorder_by_ip.exists() and obj in [_.item for _ in preorder_by_ip]:
        obj.is_for_preorder = False
        preorder_by_ip.delete()

    elif preorder_by_ip.exists() and not obj in [_.item for _ in preorder_by_ip]:
        obj.is_for_preorder = True
        PreOrder.objects.create(item=obj, quantity=quantity, client_ip=client_ip)
    obj.save()
    return redirect(reverse('trade:trade_detail', kwargs={'pk': obj.pk}))


def pre_order_detail(request):
    """Редактирование корзины. Добавил формсеты, чтобы была возможность удаления продукта из корзины, восстановления
    статуса False для is_for_preorder"""
    pre_order_formset = modelformset_factory(PreOrder, fields=['quantity'], extra=0, can_delete=True,
                                             widgets={'quantity': forms.NumberInput(attrs={'min': 1}, )
                                                      })
    currencies = Currency.objects.all()
    total_sum = 0
    if request.method == 'POST':
        formset = pre_order_formset(request.POST, queryset=PreOrder.objects.all())
        if formset.is_valid():
            instances = formset.save(commit=False)  # без commit=False не будет работать удаление
            # Блок проверки удаленных объектов
            for deleted_obj in formset.deleted_objects:
                item = deleted_obj.item
                if not PreOrder.objects.filter(item=item).exclude(pk=deleted_obj.pk).exists():
                    item.is_for_preorder = False
                    item.save()
                deleted_obj.delete()
            # Сохранение изменений в БД
            for instance in instances:
                instance.save()

            # Блок расчета итоговой суммы в указанной валюте
            currency = get_object_or_404(Currency, id=request.POST.get('currency'))
            for pre_order in formset.queryset:
                pre_order.currency_pay = currency  # сохраняем выбранный курс валюты расчета в БД
                pre_order.save()
                if pre_order.item.currency == currency:
                    total_sum += pre_order.item.price + pre_order.item.price * get_object_or_404(Tax,
                    name='НДС').tax_base / pre_order.item.price * pre_order.quantity
                else:
                    total_sum += (pre_order.item.price + (pre_order.item.price * get_object_or_404(Tax,
                    name='НДС').tax_base / 100)) * pre_order.quantity / get_object_or_404(
                    Currency, related_currency=currency.code).value

    else:
        formset = pre_order_formset(queryset=PreOrder.objects.all())

    return render(request, template_name='trade/preorder_detail.html', context={'formset': formset,
                                                                                'currencies': currencies,
                                                                                'total_sum': total_sum,
                                                                                'tax': Tax.objects.filter(name='НДС')[0]})


def get_payment_session(request):
    """Метод для получения сессии оплаты. Более корректный метод определения нужно товара в корзине по IP,
    но в нашем случае, по условиям задачи это не предусмотрено. Поэтому, отбор нужным продуктов из корзины будет
    по условию - ВСЕ. В реальной жизни, я бы вместо хэширования в модели PreOrder оставил GenericIPAddressField,
    затем уже при отборе товаров отбирал по IP"""
    obj = PreOrder.objects.all()
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
