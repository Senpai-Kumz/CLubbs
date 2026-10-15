import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """Authenticated WebSocket consumer for one Clubb conversation."""

    async def connect(self):
        self.conversation_id = int(self.scope["url_route"]["kwargs"]["conversation_id"])
        self.room_group_name = f"clubb_chat_{self.conversation_id}"
        self.group_joined = False
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        if not await self._is_conversation_member():
            # A user must be a participant to read or write to this room.
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.group_joined = True
        await self.accept()

    async def disconnect(self, close_code):
        if getattr(self, "group_joined", False):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self._send_error("Invalid message payload.")
            return

        if payload.get("type") != "message":
            return

        content = payload.get("content", "")
        if not isinstance(content, str):
            await self._send_error("Message text must be a string.")
            return

        content = content.strip()
        if not content:
            return
        if len(content) > 4000:
            await self._send_error("Messages must be 4,000 characters or fewer.")
            return

        message_data = await self._save_message(content)
        if message_data is None:
            await self._send_error("You no longer have access to this conversation.")
            await self.close(code=4403)
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "payload": message_data,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"type": "chat_message", **event["payload"]}))

    async def _send_error(self, message):
        await self.send(text_data=json.dumps({"type": "error", "message": message}))

    @database_sync_to_async
    def _is_conversation_member(self):
        user = self.scope["user"]
        return Conversation.objects.filter(
            pk=self.conversation_id,
            participants=user,
        ).exists()

    @database_sync_to_async
    def _save_message(self, content):
        user = self.scope["user"]
        conversation = (
            Conversation.objects
            .filter(pk=self.conversation_id, participants=user)
            .first()
        )
        if conversation is None:
            return None

        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content,
        )
        # Refresh updated_at so this conversation sorts to the top on next page load.
        conversation.save(update_fields=["updated_at"])

        return {
            "message_id": message.pk,
            "conversation_id": conversation.pk,
            "sender_id": user.pk,
            "sender_username": user.username,
            "content": message.content,
            "created_at": timezone.localtime(message.created_at).isoformat(),
        }
