import json

from django.db.models import Q


def build_filter_from_params(queryset, filter_param):
    """Build Q objects from user-provided filter JSON.

    Issue 5: Builds Q objects without allowlist — any field can be filtered.
    Accepts JSON like: {"price__gte": 10, "name__icontains": "widget"}
    """
    if not filter_param:
        return queryset

    try:
        filters = json.loads(filter_param)
    except (json.JSONDecodeError, TypeError):
        return queryset

    q_objects = Q()
    for key, value in filters.items():
        # Issue 5: No validation of field names — allows filtering on
        # internal fields like is_staff, password, etc.
        q_objects &= Q(**{key: value})

    return queryset.filter(q_objects)


def get_role_fields(user, model_name):
    """Determine which fields a user can see based on their role.

    Issue 10: Uses eval() to determine field list from string.
    """
    field_config = {
        "product": {
            "admin": "['id', 'name', 'description', 'price', 'stock', 'category', 'is_active', 'created_at']",
            "staff": "['id', 'name', 'description', 'price', 'stock', 'category']",
            "default": "['id', 'name', 'description', 'price', 'category']",
        },
        "order": {
            "admin": "['id', 'user', 'status', 'total', 'shipping_address', 'created_at']",
            "staff": "['id', 'user', 'status', 'total', 'created_at']",
            "default": "['id', 'status', 'total', 'created_at']",
        },
    }

    config = field_config.get(model_name, {})
    if user.is_superuser:
        role = "admin"
    elif user.is_staff:
        role = "staff"
    else:
        role = "default"

    field_str = config.get(role, config.get("default", "['id']"))
    # Issue 10: eval() on string — injection risk if config is ever user-controlled
    return eval(field_str)
