"""
urls.py — App URL Routing

DRF's Router auto-generates all standard REST URLs for our ViewSets.

Registered routes become:
  /api/tasks/                    → list + create
  /api/tasks/<id>/               → retrieve, update, delete
  /api/tasks/<id>/toggle-status/ → mark complete/incomplete
  /api/tasks/summary/            → task counts
  /api/users/                    → register
  /api/users/me/                 → your own profile
  /api/users/change-password/    → change password
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, UserViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
