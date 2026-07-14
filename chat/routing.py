from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # a separate room per user (e.g. for user with id 5 => ws/chat/user_5/)
    re_path(r"ws/chat/user_(?P<user_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
]
