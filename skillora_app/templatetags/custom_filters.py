from django import template
from django.conf import settings
from django.core.files.storage import default_storage

from skillora_app.models import Course  # type: ignore
from skillora_app.course_utils import get_course_image_path

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


@register.filter(name='course_image_url')
def course_image_url(course: Course) -> str:
    """Return a safe URL for a course image, preferring uploaded file when it exists,
    otherwise falling back to a static image path derived from the title.
    """
    try:
        if getattr(course, 'image', None) and getattr(course.image, 'name', ''):
            # Only use uploaded image if it actually exists on disk/storage
            if default_storage.exists(course.image.name):
                return course.image.url
    except Exception:
        pass

    static_rel = get_course_image_path(getattr(course, 'title', '') or '')
    if static_rel:
        return settings.STATIC_URL.rstrip('/') + '/' + static_rel.lstrip('/')
    # fallback generic image
    return settings.STATIC_URL.rstrip('/') + '/img/courses/course-1.jpg'

