"""
Root URL Configuration.

All requests come here first. Django matches the URL
and forwards to the right view or app.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # POST /api/auth/login/
    TokenRefreshView,      # POST /api/auth/refresh/
)

urlpatterns = [
    # Django admin dashboard
    path('admin/', admin.site.urls),

    # Authentication — get and refresh JWT tokens
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # All task and user endpoints (defined in task_manager/urls.py)
    path('api/', include('task_manager.urls')),
]
