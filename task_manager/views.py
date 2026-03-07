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


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'priority', 'created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        # This is the key security line users only ever see their own tasks
        return Task.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='toggle-status', url_name='toggle-status')
    def toggle_status(self, request, pk=None):
        task = self.get_object()

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

        task_serializer = TaskSerializer(task, context={'request': request})
        return Response({'message': message, 'task': task_serializer.data})

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        from django.utils import timezone
        queryset = self.get_queryset()

        return Response({
            'total': queryset.count(),
            'pending': queryset.filter(status=Status.PENDING).count(),
            'completed': queryset.filter(status=Status.COMPLETED).count(),
            'overdue': queryset.filter(
                status=Status.PENDING,
                due_date__lt=timezone.now()
            ).count(),
        })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]

    def get_serializer_class(self):
        # Registration needs a different serializer because it handles passwords
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            # Anyone can register no token needed
            return [AllowAny()]
        elif self.action == 'list':
            from rest_framework.permissions import IsAdminUser
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsSelfOrAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        output_serializer = UserSerializer(user, context={'request': request})
        return Response(
            {
                'message': 'Account created. Please log in to get your token.',
                'user': output_serializer.data,
            },
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get', 'put', 'patch', 'delete'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user

        if request.method == 'GET':
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data)

        elif request.method in ('PUT', 'PATCH'):
            partial = request.method == 'PATCH'
            serializer = UserSerializer(user, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == 'DELETE':
            user.delete()
            return Response({'message': 'Account deleted.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='change-password', permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # set_password handles hashing never store passwords as plain text
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({'message': 'Password changed. Please log in again.'})
