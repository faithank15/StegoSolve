import base64
from io import BytesIO
from django import template

register = template.Library()

@register.filter
def image_to_base64(img):
    buf = BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()