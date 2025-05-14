from django.shortcuts import render
from djangorestframwork import viewsets
from .models import Post

# Create your views here.
class PostViewset(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
