from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),  # Pour login, register, profile...
    path('api/employees/', include('hr_employees.urls')),  # Pour les employés
]
