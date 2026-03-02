"""
serializers.py — Data Serialization

Serializers do two things:
  1. Convert Python objects → JSON (for API responses)
  2. Convert JSON → validated Python data → save to DB

They also handle all input VALIDATION.
"""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from .models import Task, Priority, Status


# ─── USER SERIALIZERS ─────────────────────────────────────────────────────────

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Used for creating a new user account (POST /api/users/)."""

    password = serializers.CharField(
        write_only=True,            # Never returned in responses
        required=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        """
        Use create_user() NOT create() — it hashes the password.
        Never store plain text passwords!
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Used for reading and updating user profiles. No password field."""

    # Extra computed field showing how many tasks this user has
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'task_count']
        read_only_fields = ['id', 'date_joined']

    def get_task_count(self, obj):
        """SerializerMethodField calls get_<fieldname>(self, obj)."""
        return obj.tasks.count()


class ChangePasswordSerializer(serializers.Serializer):
    """Used for changing a user's password."""

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    def validate_old_password(self, value):
        """Check the old password is actually correct before allowing change."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


# ─── TASK SERIALIZERS ─────────────────────────────────────────────────────────

class TaskSerializer(serializers.ModelSerializer):
    """
    Main serializer for Tasks.
    Handles create, read, update, delete.
    """

    # Read-only computed fields from model @property methods
    is_overdue = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    # Show owner's username instead of their numeric ID
    owner = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'owner', 'title', 'description', 'due_date',
            'priority', 'status', 'completed_at', 'is_completed',
            'is_overdue', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'completed_at', 'created_at', 'updated_at']

    def validate_due_date(self, value):
        """Due date must be in the future."""
        if value <= timezone.now():
            raise serializers.ValidationError("Due date must be in the future.")
        return value

    def validate_priority(self, value):
        """Priority must be LOW, MEDIUM, or HIGH."""
        valid = [choice[0] for choice in Priority.choices]
        if value not in valid:
            raise serializers.ValidationError(
                f"Priority must be one of: {', '.join(valid)}"
            )
        return value

    def validate(self, data):
        """
        Object-level validation — runs after all field validations.
        Prevents editing completed tasks (except to change status).
        """
        if self.instance is not None:           # Only on updates, not creates
            if self.instance.is_completed:
                allowed_fields = {'status'}
                changed_fields = set(data.keys()) - allowed_fields
                if changed_fields:
                    raise serializers.ValidationError(
                        f"Completed tasks cannot be edited. "
                        f"Revert to PENDING first. "
                        f"Fields attempted: {', '.join(changed_fields)}"
                    )
        return data

    def create(self, validated_data):
        """Auto-assign the logged-in user as task owner on creation."""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Handle status changes specially:
        - PENDING → COMPLETED: call mark_complete() to set the timestamp
        - COMPLETED → PENDING: call mark_incomplete() to clear the timestamp
        """
        new_status = validated_data.get('status', instance.status)

        if new_status == Status.COMPLETED and not instance.is_completed:
            instance.mark_complete()
            validated_data.pop('status', None)
        elif new_status == Status.PENDING and instance.is_completed:
            instance.mark_incomplete()
            validated_data.pop('status', None)

        return super().update(instance, validated_data)


class TaskStatusSerializer(serializers.Serializer):
    """
    Minimal serializer for the toggle-status endpoint.
    Only accepts a status field — nothing else.
    """
    status = serializers.ChoiceField(choices=Status.choices, required=True)
