"""
Serializers for users app - aligned to API-001, API-002, API-004.

API-001 Registration: npm_nip, nama, email, password, unit_gedung
API-002 Login: identifier (npm_nip OR email) + password
API-004 Profile: returns user_id, nama, email, peran, unit_gedung, total_poin
"""
import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    API-001 - Register.
    Role is forced to 'civitas' server-side (TC-006: prevent role injection).
    """
    npm_nip = serializers.CharField(max_length=20, required=True)
    name = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(max_length=100, required=True)
    unit_gedung = serializers.CharField(max_length=50, required=True)
    password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ('npm_nip', 'name', 'email', 'unit_gedung', 'password')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email sudah terdaftar dalam sistem.')
        return value.lower()

    def validate_npm_nip(self, value):
        if User.objects.filter(npm_nip=value).exists():
            raise serializers.ValidationError('NPM/NIP sudah terdaftar dalam sistem.')
        return value

    def create(self, validated_data):
        # Server-side: role hardcoded to civitas (defense against client tampering, TC-006)
        user = User.objects.create_user(
            npm_nip=validated_data['npm_nip'],
            name=validated_data['name'],
            email=validated_data['email'],
            unit_gedung=validated_data['unit_gedung'],
            password=validated_data['password'],
        )
        logger.info(f"New civitas registered: {user.email} ({user.npm_nip})")
        return user


class UserSerializer(serializers.ModelSerializer):
    """API-002 / API-004 - full profile response."""

    class Meta:
        model = User
        fields = ('id', 'npm_nip', 'name', 'email', 'role', 'unit_gedung', 'total_poin', 'created_at', 'is_active')
        read_only_fields = ('id', 'total_poin', 'role', 'created_at', 'is_active')


class LoginSerializer(serializers.Serializer):
    """
    API-002 - Login. Accepts NPM/NIP OR email as identifier.
    """
    identifier = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        identifier = attrs.get('identifier', '').strip().lower()
        password = attrs.get('password')

        if not identifier or not password:
            raise serializers.ValidationError('NPM/NIP/Email dan kata sandi wajib diisi.')

        # Try matching by email first, fall back to npm_nip
        user = None
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(npm_nip__iexact=identifier).first()
            # if not found by npm_nip, also try as email in case they entered email without @
            if not user:
                user = User.objects.filter(email__iexact=identifier).first()

        if user is None or not user.check_password(password):
            # Single uniform error to avoid leaking which identifier was registered (TC-009)
            raise serializers.ValidationError('NPM/NIP/Email atau kata sandi tidak valid.')

        if not user.is_active:
            raise serializers.ValidationError('Akun ini tidak aktif.')

        attrs['user'] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """API-004 - update profile (only name, unit_gedung). Cannot change role/email."""

    class Meta:
        model = User
        fields = ('name', 'unit_gedung')
