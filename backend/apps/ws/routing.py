from django.urls import re_path
from apps.ws.consumers import SearchConsumer, AlertConsumer

websocket_urlpatterns = [
    re_path(r"^ws/search/(?P<search_id>\d+)/$", SearchConsumer.as_asgi()),
    re_path(r"^ws/alerts/$", AlertConsumer.as_asgi()),
]
