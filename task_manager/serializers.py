from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from .models import Task, Priority, Status


class UserRegistrationSerializer(serializers.ModelSerializer):
    # write_only means this field is accepted on input but never returned in responses
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        # Always use create_user() it hashes the password automatically
        # Using create() directly would store it as plain text
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    # Shows how many tasks this user has without exposing the actual task data
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'task_count']
        read_only_fields = ['id', 'date_joined']

    def get_task_count(self, obj):
        return obj.tasks.count()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    def validate_old_password(self, value):
        # Pull the user from the request context and check their current password
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class TaskSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    # Show the username instead of just the user ID
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
        if value <= timezone.now():
            raise serializers.ValidationError("Due date must be in the future.")
        return value

    def validate_priority(self, value):
        valid_priorities = [choice[0] for choice in Priority.choices]
        if value not in valid_priorities:
            raise serializers.ValidationError(
                f"Priority must be one of: {', '.join(valid_priorities)}"
            )
        return value

    def validate(self, data):
        # Block edits on completed tasks the user needs to revert it to PENDING first
        if self.instance is not None:
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
        # Assign the loggedin user as the task owner automatically
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)

        if new_status == Status.COMPLETED and not instance.is_completed:
            # Use the model method so completed_at gets set properly
            instance.mark_complete()
            validated_data.pop('status', None)

        elif new_status == Status.PENDING and instance.is_completed:
            instance.mark_incomplete()
            validated_data.pop('status', None)

        return super().update(instance, validated_data)


class TaskStatusSerializer(serializers.Serializer):
    # Minimal serializer just for the toggle status endpoint
    status = serializers.ChoiceField(choices=Status.choices, required=True)
