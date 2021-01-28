from .models import User, Camera, Video
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'id')
        
class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ('name', 'id', 'url')
        
class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('finish', 'id', 'status_item', 'user', 'camera', 'created_at')
