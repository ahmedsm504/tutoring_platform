from django import template

register = template.Library()

@register.filter
def intcomma(value):
    """Convert integer to string with commas"""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value