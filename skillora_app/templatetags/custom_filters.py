from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(mapping, key):
    """Return mapping[key] for dict-like objects. Tries both str and int keys."""
    if mapping is None:
        return None
    try:
        # Try direct key
        if key in mapping:
            return mapping.get(key)
    except Exception:
        pass
    # Try stringified versions
    try:
        return mapping.get(str(key))
    except Exception:
        return None


