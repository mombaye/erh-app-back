from rest_framework import serializers
from .models import BulletinEnvoiLog, Employee

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'


# Serializer minimal pour les logs d’envoi de bulletin
class BulletinEnvoiLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulletinEnvoiLog
        fields = ["matricule", "email", "statut", "message", "date_envoi"]