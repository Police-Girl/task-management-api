"""
views.py — API Endpoint Handlers

Views receive HTTP requests, process them, and return responses.

ViewSet actions map to HTTP methods:
  list()           → GET    /api/tasks/
  create()         → POST   /api/tasks/
  retrieve()       → GET    /api/tasks/<id>/
  update()         → PUT    /api/tasks/<id>/
  partial_update() → PATCH  /api/tasks/<id>/
  destroy()        → DELETE /api/tasks/<id>/
"""

from django.contrib.auth.models import User
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Task, Status
from .serializers import (
    TaskSerializer, TaskStatusSerializer,
    UserSerializer, UserRegistrationSerializer, ChangePasswordSerializer,
)
from .permissions import IsOwner, IsSelfOrAdmin
from .filters import TaskFilter


# ─── TASK VIEWSET ─────────────────────────────────────────────────────────────

class TaskViewSet(viewsets.ModelViewSet):
    """
    Full CRUD API for Tasks.
    Users can only see and manage their OWN tasks.
    """

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    # These handle ?status=, ?ordering=, ?search= URL parameters
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']         # ?search=keyword
    ordering_fields = ['due_date', 'priority', 'created_at', 'status']
    ordering = ['-created_at']                        # Default sort

    def get_queryset(self):
        """
        CRITICAL SECURITY: Only return tasks belonging to the logged-in user.
        This is the main line that prevents users seeing each other's tasks.
        """
        return Task.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Mark a task complete or incomplete.
        POST /api/tasks/<id>/toggle-status/
        Body: {"status": "COMPLETED"} or {"status": "PENDING"}
        """
        task = self.get_object()  # Also checks ownership permission

        serializer = TaskStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']

        if new_status == Status.COMPLETED:
            task.mark_complete()
            message = "Task marked as completed."
        else:
            task.mark_incomplete()
            message = "Task reverted to pending."

        task_data = TaskSerializer(task, context={'request': request})
        return Response({'message': message, 'task': task_data.data})

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Quick overview of task counts.
        GET /api/tasks/summary/
        """
        queryset = self.get_queryset()
        from django.utils import timezone

        return Response({
            'total': queryset.count(),
            'pending': queryset.filter(status=Status.PENDING).count(),
            'completed': queryset.filter(status=Status.COMPLETED).count(),
            'overdue': queryset.filter(
                status=Status.PENDING,
                due_date__lt=timezone.now()
            ).count(),
        })


# ─── USER VIEWSET ─────────────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    """User management — register, view, update, delete accounts."""

    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]

    def get_serializer_class(self):
        """Use different serializers depending on the action."""
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserSerializer

    def get_permissions(self):
        """Override permissions per action."""
        if self.action == 'create':
            return [AllowAny()]             # Anyone can register
        elif self.action == 'list':
            from rest_framework.permissions import IsAdminUser
            return [IsAuthenticated(), IsAdminUser()]  # Admin only
        return [IsAuthenticated(), IsSelfOrAdmin()]

    def create(self, request, *args, **kwargs):
        """POST /api/users/ — Register a new user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        output = UserSerializer(user, context={'request': request})
        return Response(
            {'message': 'Account created. Please log in to get your token.', 'user': output.data},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get', 'put', 'patch', 'delete'],
            url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        /api/users/me/ — manage your own account without knowing your ID.
        GET = view, PUT/PATCH = update, DELETE = delete account.
        """
        user = request.user

        if request.method == 'GET':
            return Response(UserSerializer(user, context={'request': request}).data)

        elif request.method in ('PUT', 'PATCH'):
            partial = request.method == 'PATCH'
            serializer = UserSerializer(user, data=request.data, partial=partial,
                                        context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == 'DELETE':
            user.delete()
            return Response({'message': 'Account deleted.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='change-password',
            permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """POST /api/users/change-password/ — change your password."""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password changed. Please log in again.'})
