from rest_framework import serializers 
from .models import BlogPost


class PostSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    pub_date = serializers.DateTimeField()
    author = serializers.CharField(max_length=100)