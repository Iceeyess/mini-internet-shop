from unicodedata import decimal

from django import template

register = template.Library()

@register.filter
def multiply(value, tax):
    try:
        return f'{round(value + value * tax / 100, 2):.2f}'
    except (ValueError, TypeError):
        return 'Проверьте введенные данные цены и налога.'

@register.simple_tag
def total_item_amount(value, tax, quantity):
    try:
        return f'{round(value + value * tax / 100 * quantity, 2):.2f}'
    except (ValueError, TypeError):
        return 'Проверьте введенные данные цены, налога и количества.'