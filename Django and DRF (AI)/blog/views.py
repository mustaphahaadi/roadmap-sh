# views.py
from rest_framework import generics
from .models import Post
from .serializers import PostSerializer

class PostList(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class PostDetail(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class PostCreate(generics.CreateAPIView):
    serializer_class = PostSerializer

class PostUpdate(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class PostDelete(generics.DestroyAPIView):
    queryset = Post.objects.all()