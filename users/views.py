import logging
from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.IsAuthenticated]  # Seul un admin peut créer un utilisateur



logger = logging.getLogger(__name__)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logger.info(f"Utilisateur connecté : {request.user}")
        return Response(UserSerializer(request.user).data)


class CustomTokenObtainPairView(TokenObtainPairView):
    # Utilise le serializer par défaut, mais tu peux en personnaliser un si besoin
    pass



class ChangePasswordView(APIView):
    """
    Permet à l'utilisateur connecté de changer son mot de passe.
    Met aussi first_login à False si c'était le premier login.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            return Response({"error": "Tous les champs sont obligatoires."}, status=400)
        if new_password != confirm_password:
            return Response({"error": "Les mots de passe ne correspondent pas."}, status=400)
        if not user.check_password(old_password):
            return Response({"error": "Ancien mot de passe incorrect."}, status=400)

        user.set_password(new_password)
        user.first_login = False
        user.save()
        return Response({"message": "Mot de passe changé avec succès. Vous pouvez vous reconnecter."}, status=200)
