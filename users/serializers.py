from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Inscription d'un nouveau client."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'password',
            'first_name', 'last_name', 'telephone', 'region',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            role=CustomUser.Role.CLIENT,
            **validated_data,
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Profil complet d'un utilisateur connecté."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name',
            'telephone', 'region', 'region_display',
            'role', 'role_display',
            'revenu_mensuel',
            'date_joined',
        ]
        read_only_fields = ['id', 'username', 'role', 'date_joined']


class UserListSerializer(serializers.ModelSerializer):
    """Résumé pour les listes (agents, dashboard)."""
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'role', 'region', 'telephone']
