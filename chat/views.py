from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .models import Conversation, Message
from .serializers import ConversationSerializer, ConversationDetailSerializer, MessageSerializer
from users.permissions import IsAdminOrAgent


@extend_schema(tags=['Chat'])
class ConversationViewSet(viewsets.ModelViewSet):
    """
    Conversations de support client.

    - CLIENT : crée et consulte ses propres conversations.
    - AGENT/ADMIN : consulte toutes les conversations, peut s'assigner.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Conversation.objects.select_related('client', 'agent')
        if user.role == 'CLIENT':
            return qs.filter(client=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'CLIENT':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les clients peuvent ouvrir une conversation.")
        conversation = serializer.save(client=user)

    @extend_schema(responses={200: ConversationSerializer})
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAgent], url_path='assigner')
    def assigner(self, request, pk=None):
        """Assigner l'agent courant à cette conversation."""
        conv = self.get_object()
        conv.agent = request.user
        conv.save()
        return Response(ConversationSerializer(conv).data)

    @extend_schema(responses={200: ConversationSerializer})
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAgent], url_path='fermer')
    def fermer(self, request, pk=None):
        """Fermer une conversation."""
        conv = self.get_object()
        conv.fermer()
        return Response(ConversationSerializer(conv).data)

    @extend_schema(responses={200: MessageSerializer(many=True)})
    @action(detail=True, methods=['get'], url_path='messages')
    def get_messages(self, request, pk=None):
        """Historique des messages d'une conversation (paginé)."""
        conv = self.get_object()
        msgs = conv.messages.order_by('envoye_le')
        return Response(MessageSerializer(msgs, many=True).data)


# ─── WEB VIEWS ────────────────────────────────────────────────────────────────

@login_required(login_url='login_web')
def lancer_chat_web(request):
    """Créer une nouvelle conversation et rediriger vers l'interface chat."""
    if request.user.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent ouvrir une conversation.")
        return redirect('home_web')
    sujet = request.POST.get('sujet', 'Demande de support')
    conv = Conversation.objects.create(client=request.user, sujet=sujet)
    return redirect('chat_detail_web', conv_id=conv.id)


@login_required(login_url='login_web')
def chat_detail_web(request, conv_id):
    """Interface de chat en temps réel (WebSocket)."""
    conv = get_object_or_404(Conversation, id=conv_id)

    # Vérifier les droits d'accès
    if request.user.role == 'CLIENT' and conv.client != request.user:
        messages.error(request, "Accès non autorisé.")
        return redirect('home_web')

    # L'agent s'assigne automatiquement à l'ouverture si la conv est sans agent
    if request.user.role in ('AGENT', 'ADMIN') and not conv.agent:
        conv.agent = request.user
        conv.save()

    historique = conv.messages.order_by('envoye_le')
    return render(request, 'chat.html', {
        'conversation': conv,
        'historique': historique,
        'user': request.user,
    })


@login_required(login_url='login_web')
def conversations_list_web(request):
    """Liste des conversations pour les agents/admins."""
    if request.user.role == 'CLIENT':
        return redirect('home_web')
    convs = Conversation.objects.filter(statut='OUVERTE').select_related('client', 'agent').order_by('-cree_le')
    return render(request, 'conversations.html', {'conversations': convs})
