from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import BulletinEnvoiLog, Employee

User = get_user_model()

class EmployeeSerializer(serializers.ModelSerializer):
    has_user = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()  # Optionnel

    class Meta:
        model = Employee
        fields = '__all__'  # Tous les champs natifs du modèle Employee
        extra_fields = ['has_user', 'user_id']     # Pour info, pas obligatoire

    def get_has_user(self, obj):
        return User.objects.filter(employee=obj).exists()

    def get_user_id(self, obj):
        user = User.objects.filter(employee=obj).first()
        return user.id if user else None

# Serializer minimal pour les logs d’envoi de bulletin
class BulletinEnvoiLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulletinEnvoiLog
        fields = ["matricule", "email", "statut", "message", "date_envoi"]
