from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet,
    lancer_chat_web,
    chat_detail_web,
    conversations_list_web,
)

router = DefaultRouter()
router.register(r'api/conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/creer/', lancer_chat_web, name='lancer_chat_web'),
    path('chat/<int:conv_id>/', chat_detail_web, name='chat_detail_web'),
    path('conversations/', conversations_list_web, name='conversations_list_web'),
]
