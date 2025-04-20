from django import template

register = template.Library()

@register.filter
def dictvalue(dictionary, key):
    """Retrieve a value from a dictionary by key."""
    return dictionary.get(key, 0)

def percentage_discount(price, sale_price):
    if price > 0 and sale_price:
        return int(((price - sale_price) / price) * 100)
    return 0