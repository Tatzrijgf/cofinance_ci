from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_notif_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'titre', 'message', 'type_notif', 'type_display', 'lu', 'cree_le']
        read_only_fields = ['id', 'cree_le']
