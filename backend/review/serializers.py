from rest_framework import serializers

from .models import ReviewAction


class ReviewActionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = ReviewAction
        fields = ["id", "action", "comment", "actor_name", "created_at"]
