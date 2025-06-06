from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from recipes.models import Recipe
import base64
import uuid
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        read_only_fields = ('email', 'id', 'username', 'first_name',
                           'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.subscriptions.filter(author=obj).exists()
        return False
        
    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None


class SubscribedAuthorSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count', 'avatar')
        read_only_fields = ('email', 'id', 'username', 'first_name',
                           'last_name', 'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        from api.serializers.recipes import RecipeSerializer
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return RecipeSerializer(recipes, many=True, context=self.context).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        request = self.context.get('request')
        if instance.avatar and hasattr(instance.avatar, 'url'):
            return {
                'avatar': request.build_absolute_uri(instance.avatar.url)
            }
        return {'avatar': None}
        
    def validate_avatar(self, value):
        if not value or not isinstance(value, str):
            raise serializers.ValidationError('Некорректный формат данных')
            
        if 'data:' not in value or ';base64,' not in value:
            raise serializers.ValidationError('Строка не соответствует формату data:mime;base64,')
            
        return value

    def update(self, instance, validated_data):
        avatar_data = validated_data.get('avatar')
        
        format, imgstr = avatar_data.split(';base64,')
        ext = format.split('/')[-1]
        
        file_name = f"{uuid.uuid4()}.{ext}"
        
        data = ContentFile(base64.b64decode(imgstr), name=file_name)
        
        if instance.avatar:
            instance.avatar.delete()
            
        instance.avatar = data
        instance.save()
        
        return instance