from django import template

register = template.Library()

@register.filter
def multiply(value, tax):
    try:
        return round(value + value * tax / 100, 2)
    except (ValueError, TypeError):
        return 'Проверьте введенные данные цены и налога.'