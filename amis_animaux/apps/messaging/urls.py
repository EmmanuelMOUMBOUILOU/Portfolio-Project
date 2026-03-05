from django.urls import path
from .views import ConversationListCreateView, MessageListCreateView

urlpatterns = [
    path("conversations/", ConversationListCreateView.as_view(), name="conversation_list_create"),
    path("conversations/<int:conversation_id>/messages/", MessageListCreateView.as_view(), name="message_list_create"),
]
