import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consommateur WebSocket pour le chat de support en temps réel.

    Protocole JSON :
    ─────────────────────────────────────────────────────────────────
    Envoi (client → serveur) :
        {"type": "message",  "content": "Bonjour",  "sender_id": 42}
        {"type": "typing",   "state": "on"|"off",   "sender_id": 42}
        {"type": "join"}   ← connexion initiale

    Réception (serveur → client) :
        {"type": "message",  "content": "...", "sender_id": 42, "sender_nom": "...",
         "timestamp": "...", "message_id": 7}
        {"type": "typing",   "state": "on",  "sender_id": 42, "sender_nom": "..."}
        {"type": "presence", "user_id": 42,  "online": true}
        {"type": "error",    "detail": "..."}
    ─────────────────────────────────────────────────────────────────
    """

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Vérifier que la conversation existe
        valid = await self.check_conversation_exists(self.conversation_id)
        if not valid:
            await self.close(code=4004)
            return

        # Rejoindre le groupe du canal
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        # Diffuser la présence
        sender_id = self.scope['query_string']
        user_id = await self._get_user_id_from_query()
        if user_id:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_update',
                    'user_id': user_id,
                    'online': True,
                }
            )

    async def disconnect(self, close_code):
        user_id = await self._get_user_id_from_query()
        if user_id:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_update',
                    'user_id': user_id,
                    'online': False,
                }
            )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'type': 'error', 'detail': 'JSON invalide'}))
            return

        msg_type = data.get('type', 'message')
        sender_id = data.get('sender_id')

        if msg_type == 'message':
            content = data.get('content', '').strip()
            if not content:
                return
            if not sender_id:
                await self.send(text_data=json.dumps({'type': 'error', 'detail': 'sender_id requis'}))
                return

            # Sauvegarder en base de données
            saved = await self.save_message(sender_id, self.conversation_id, content)
            if not saved:
                await self.send(text_data=json.dumps({'type': 'error', 'detail': 'Utilisateur ou conversation invalide'}))
                return

            message_id, sender_nom, timestamp = saved

            # Diffuser à tous les membres du groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'content': content,
                    'sender_id': sender_id,
                    'sender_nom': sender_nom,
                    'timestamp': timestamp,
                    'message_id': message_id,
                }
            )

        elif msg_type == 'typing':
            state = data.get('state', 'on')
            sender_nom = await self.get_user_name(sender_id) if sender_id else 'Inconnu'
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'sender_id': sender_id,
                    'sender_nom': sender_nom,
                    'state': state,
                }
            )

    # ── Gestionnaires de messages de groupe ──────────────────────────────────

    async def chat_message(self, event):
        """Relayer un message au WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_nom': event['sender_nom'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
        }))

    async def typing_indicator(self, event):
        """Relayer l'indicateur de frappe."""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'sender_nom': event['sender_nom'],
            'state': event['state'],
        }))

    async def presence_update(self, event):
        """Relayer la mise à jour de présence."""
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'online': event['online'],
        }))

    # ── Méthodes synchrones appelées via database_sync_to_async ─────────────

    @database_sync_to_async
    def check_conversation_exists(self, conversation_id):
        from .models import Conversation
        return Conversation.objects.filter(id=conversation_id).exists()

    @database_sync_to_async
    def save_message(self, user_id, conversation_id, content):
        from users.models import CustomUser
        from .models import Conversation, Message
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            user = CustomUser.objects.get(id=user_id)
            msg = Message.objects.create(
                conversation=conversation,
                expediteur=user,
                contenu=content,
            )
            nom = user.get_full_name() or user.username
            ts = msg.envoye_le.strftime('%H:%M')
            return msg.id, nom, ts
        except Exception:
            return None

    @database_sync_to_async
    def get_user_name(self, user_id):
        from users.models import CustomUser
        try:
            u = CustomUser.objects.get(id=user_id)
            return u.get_full_name() or u.username
        except Exception:
            return 'Inconnu'

    async def _get_user_id_from_query(self):
        """Extrait l'ID utilisateur depuis la query string (?user_id=XX)."""
        query_string = self.scope.get('query_string', b'').decode()
        for param in query_string.split('&'):
            if param.startswith('user_id='):
                try:
                    return int(param.split('=')[1])
                except ValueError:
                    return None
        return None
