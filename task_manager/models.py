from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# I'm using TextChoices here so the database stores readable strings
# instead of integers easier to debug when you're looking at raw data
class Priority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'


class Status(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'


class Task(models.Model):
    # Each task belongs to one user  if the user gets deleted, their tasks go too
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    due_date = models.DateTimeField()

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Only gets set when the task is marked complete stays null otherwise
    completed_at = models.DateTimeField(null=True, blank=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        # These indexes speed up the most common queries
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'due_date']),
        ]

    def __str__(self):
        return f"[{self.priority}] {self.title} — {self.status}"

    def mark_complete(self):
        self.status = Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def mark_incomplete(self):
        # Clear the timestamp when reverting  it shouldn't stick around
        self.status = Status.PENDING
        self.completed_at = None
        self.save()

    @property
    def is_completed(self):
        return self.status == Status.COMPLETED

    @property
    def is_overdue(self):
        # A completed task can't be overdue even if the due date has passed
        return self.status == Status.PENDING and self.due_date < timezone.now()
