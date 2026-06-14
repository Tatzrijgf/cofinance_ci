from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.SerializerMethodField()
    expediteur_role = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'expediteur', 'expediteur_nom', 'expediteur_role',
            'contenu', 'envoye_le',
        ]
        read_only_fields = ['id', 'expediteur', 'envoye_le']

    def get_expediteur_nom(self, obj):
        return obj.expediteur.get_full_name() or obj.expediteur.username

    def get_expediteur_role(self, obj):
        return obj.expediteur.role


class ConversationSerializer(serializers.ModelSerializer):
    client_nom = serializers.SerializerMethodField()
    agent_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    nb_messages = serializers.SerializerMethodField()
    dernier_message_contenu = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'client', 'client_nom', 'agent', 'agent_nom',
            'statut', 'statut_display', 'sujet',
            'cree_le', 'ferme_le',
            'nb_messages', 'dernier_message_contenu',
        ]
        read_only_fields = ['id', 'client', 'statut', 'cree_le', 'ferme_le']

    def get_client_nom(self, obj):
        return obj.client.get_full_name() or obj.client.username

    def get_agent_nom(self, obj):
        if obj.agent:
            return obj.agent.get_full_name() or obj.agent.username
        return None

    def get_nb_messages(self, obj):
        return obj.messages.count()

    def get_dernier_message_contenu(self, obj):
        dm = obj.dernier_message
        return dm.contenu[:80] if dm else None


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']
