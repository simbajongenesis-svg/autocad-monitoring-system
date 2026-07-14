from django import template

register = template.Library()

@register.filter
def initials(value):
    """
    Turn a string into initials.
    Example: 'red blue green' -> 'RBG'
    """
    if not value:
        return ""
    return "".join(word[0].upper() for word in value.split())


@register.filter
def dict_get(d, key):
    """
    Allow Django templates to get dictionary values dynamically.
    Usage: {{ mydict|dict_get:mykey }}
    """
    if not d:
        return None
    return d.get(key)
