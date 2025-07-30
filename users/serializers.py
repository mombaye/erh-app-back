from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Country

User = get_user_model()


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code']


class UserSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_global_admin', 'country']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        request = self.context.get('request')
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            country=request.user.country if request and request.user.is_authenticated else None
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
