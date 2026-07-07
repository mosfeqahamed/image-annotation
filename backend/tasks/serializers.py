from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for the Task model."""

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'due_date', 'tags', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_tags(self, value):
        """Ensure tags is a list of strings."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        for tag in value:
            if not isinstance(tag, str):
                raise serializers.ValidationError("Each tag must be a string.")
        return value


class TaskReorderSerializer(serializers.Serializer):
    """Serializer for reordering / moving tasks between columns."""
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    order = serializers.IntegerField(min_value=0)
