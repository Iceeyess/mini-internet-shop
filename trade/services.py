from trade.models import Order


def generate_order_number() -> str:
    last_order_number = Order.objects.all().order_by('order_number').last()
    if last_order_number:
        new_order_number = str(int(last_order_number.order_number) + 1).zfill(15)
        return new_order_number
    else:
        return '1'.zfill(15)