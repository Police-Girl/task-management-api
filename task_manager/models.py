"""
models.py — Database Models

Models define your database tables.
Each class = one table. Each attribute = one column.

Relationships:
  User ──< Task   (one user has many tasks)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Priority(models.TextChoices):
    """Priority levels stored as strings in the database."""
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'


class Status(models.TextChoices):
    """Task completion status."""
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'


class Task(models.Model):
    """
    Represents a single task belonging to a user.

    Fields:
      user        → who owns this task (FK to Django's User)
      title       → short name
      description → optional detail
      due_date    → must be in the future
      priority    → LOW / MEDIUM / HIGH
      status      → PENDING / COMPLETED
      completed_at → timestamp when marked complete
      created_at  → auto-set on creation
      updated_at  → auto-updated on every save
    """

    # Link to the user who owns this task
    # on_delete=CASCADE means if user is deleted, their tasks are deleted too
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',       # Allows user.tasks.all()
    )

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True, default='')

    due_date = models.DateTimeField()

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,     # New tasks always start as PENDING
    )

    # Null means no value in the database (task not yet completed)
    completed_at = models.DateTimeField(null=True, blank=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)  # Set once on creation
    updated_at = models.DateTimeField(auto_now=True)       # Updated on every save

    class Meta:
        ordering = ['-created_at']  # Newest tasks first by default
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'due_date']),
        ]

    def __str__(self):
        return f"[{self.priority}] {self.title} — {self.status}"

    def mark_complete(self):
        """Mark task as completed and record the timestamp."""
        self.status = Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def mark_incomplete(self):
        """Revert task to pending and clear the completion timestamp."""
        self.status = Status.PENDING
        self.completed_at = None
        self.save()

    @property
    def is_completed(self):
        """Returns True if this task is completed."""
        return self.status == Status.COMPLETED

    @property
    def is_overdue(self):
        """Returns True if task is still pending but past its due date."""
        return self.status == Status.PENDING and self.due_date < timezone.now()
