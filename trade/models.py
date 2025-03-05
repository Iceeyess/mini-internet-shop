import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.


NULLABLE = dict(blank=True, null=True)


class Currency(models.Model):
    """Модель курса валют"""
    code = models.CharField(max_length=3, verbose_name='буквенный код', help_text='введите 3х-значный буквенный код')
    name = models.CharField(max_length=150, verbose_name='полное название курса', help_text='')
    related_currency = models.CharField(max_length=3, help_text='введите 3х-значный буквенный код',
                                         verbose_name='отношение текущего курса к другому', **NULLABLE)
    country = models.CharField(max_length=150, verbose_name='страна валюты', help_text='ведите страну валюты')
    value = models.FloatField(verbose_name='курс валюты')

    def __str__(self):
        return f'{self.code}'.lower()

    class Meta:
        verbose_name = 'курс валюты'
        verbose_name_plural = 'курсы валют'


class Item(models.Model):
    """Модель наименования товара"""
    name = models.CharField(max_length=250, verbose_name='наименование', help_text='введите наименование')
    description = models.TextField(verbose_name='описание', help_text='ведите описание', **NULLABLE)
    price = models.FloatField(verbose_name='цена без налога', help_text='введите цену без налога')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, verbose_name='валюта', help_text='введите валюту',
                                 **NULLABLE)
    is_for_preorder = models.BooleanField(default=False, verbose_name='признак покупки',
                                             help_text='положить в корзину?')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        ordering = ['name', ]


class Tax(models.Model):
    """Модель налогов"""
    name = models.CharField(max_length=150, verbose_name='налог', help_text='введите наименование налога')
    tax_base = models.PositiveIntegerField(verbose_name='ставка', help_text='введите ставку налога в процентах')
    stripe_tax_id = models.CharField(max_length=200, verbose_name='id номер от stripe tax rate')

    def __str__(self):
        return f'{self.name} - {self.tax_base}'

    class Meta:
        verbose_name = 'налог'
        verbose_name_plural = 'налоги'


class Discount(models.Model):
    """Модель скидок"""
    name = models.CharField(max_length=150, verbose_name='скидка', help_text='введите наименование скидки')
    discount_base = models.PositiveIntegerField(verbose_name='скидка', help_text='введите % скидки')

    def __str__(self):
        return f'{self.name} - {self.discount_base}'

    class Meta:
        verbose_name = 'скидка'
        verbose_name_plural = 'скидка'


class PreOrder(models.Model):
    """Модель корзины(предзаказ). После утверждения, модель стирается.
    Используется как промежуточная таблица.
    Можно было бы привязать к юзеру, но в нашем случае регистрация и модели юзера не предусмотрено"""
    # session_tag = models.UUIDField(default=uuid.uuid4, verbose_name='Уникальный идентификатор сессии')
    client_ip = models.GenericIPAddressField(verbose_name='IP-адрес клиента', **NULLABLE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='количество', validators=[MinValueValidator(1),
                                                                                             MaxValueValidator(10)])
    currency_pay = models.ForeignKey(Currency, on_delete=models.CASCADE, verbose_name='валюта расчета',
                                     help_text='введите валюту расчета', **NULLABLE)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='дата обновления')

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'корзины'

    def __str__(self):
        return f"Предзаказ #{self.id} ({self.item.name})"

class Order(models.Model):
    """Модель заказа"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='товар')
    quantity = models.PositiveIntegerField(verbose_name='количество')
    tax = models.ForeignKey(Tax, on_delete=models.CASCADE, verbose_name='налог')
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, verbose_name='скидка')

    def __str__(self):
        return f"Заказ #{self.id})"

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
