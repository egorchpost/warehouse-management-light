from django import template

register = template.Library()


@register.filter
def attr(obj, path):
    value = obj
    for part in str(path).split("."):
        if value is None:
            return ""
        value = getattr(value, part, "")
        if callable(value):
            value = value()
    return "" if value is None else value
