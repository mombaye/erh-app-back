from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib import admin


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # ex: 'SN', 'CI', 'ML'

    def __str__(self):
        return f"{self.name} ({self.code})"


class CustomUser(AbstractUser):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    is_global_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# --- Admin Registration ---
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_global_admin', 'country')
    list_filter = ('is_staff', 'is_global_admin', 'country')
    search_fields = ('username', 'email')
    ordering = ('username',)
