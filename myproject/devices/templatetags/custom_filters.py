from django import template

register = template.Library()

@register.filter
def dictvalue(dictionary, key):
    """Retrieve a value from a dictionary by key."""
    return dictionary.get(key, 0)