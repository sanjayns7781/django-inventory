from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer # type: ignore
from rest_framework_simplejwt.tokens import RefreshToken # type: ignore
from rest_framework.exceptions import ValidationError
import re
from .models import User, Role


class RegisterSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        queryset = Role.objects.all(),required=False

    )
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username','password','email','first_name','last_name','role_id']

    def validate(self, data):
        password = data['password']
        if len(password)<5 or len(password)>15:
            raise ValidationError("Password must be between 5 and 15 characters")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one digit")
        if not re.search(r'[@$!%*?&]', password):
            raise ValidationError("Password must contain at least one special character (@$!%*?&)")

        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        role = validated_data.pop('role_id',None)

        if not role:
            role = Role.objects.get(role_name="USER")
        else:
            if role.role_name in ["MANAGER","ADMIN"] and request.user.role.role_name != "ADMIN":
                raise ValueError("Only Admins can make the manager and Admin")
        

        user = User(
            username = validated_data['username'],
            email = validated_data['email'],
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            role = role
        )
        password = validated_data.pop('password')
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        refresh = RefreshToken.for_user(instance)
        data['access_token'] = str(refresh.access_token)
        data['refresh_token'] = str(refresh)
        data['role'] = {
            "id": instance.role.id,
            "name": instance.role.role_name
        }
        return data

class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom data here
        data.update({
            "user_id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "is_staff": self.user.is_staff,
        })

        return data

class ProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['username','email','first_name','last_name','role']

    def get_role(self, obj):
        """Return role id and role name instead of just the FK id"""
        if obj.role:  # make sure role exists
            return {
                "id": obj.role.id,
                "name": obj.role.role_name
            }
        return None

class GeminiChatSerializer(serializers.Serializer):
    message = serializers.CharField()
