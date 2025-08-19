from django.db import models

from django.contrib.auth.models import User

from item.models import Item


class Conversation(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="conversations"
    )
    members = models.ManyToManyField(User, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class ConversationMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    content = models.TextField()
    sender = models.ForeignKey(
        User, related_name="created_messages", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
