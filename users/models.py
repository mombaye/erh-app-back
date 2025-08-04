from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib import admin

from hr_employees.models import Employee


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # ex: 'SN', 'CI', 'ML'

    def __str__(self):
        return f"{self.name} ({self.code})"


class CustomUser(AbstractUser):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    is_global_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    first_login = models.BooleanField(default=False)
    employee = models.OneToOneField(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_account")

    def __str__(self):
        if self.employee:
            return f"{self.username} ({self.employee.prenom} {self.employee.nom})"
        return self.username


# --- Admin Registration ---
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_global_admin', 'first_login', 'employee','country')
    list_filter = ('is_staff', 'is_global_admin', 'country')
    search_fields = ('username', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        ('Permissions', {'fields': ('is_staff', 'is_global_admin', 'country')}),
    )
