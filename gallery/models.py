from django.db import models
from django.contrib.auth.models import User

# 1. USER IDENTITY
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    brand_color = models.CharField(max_length=7, default="#6366f1")

    def __str__(self):
        return f"{self.user.username}'s Profile"

# 2. COLLECTIONS
class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (@{self.user.username})"

# 3. CORE CONTENT
class Photo(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    # ADD blank=True, null=True to the image field
    image = models.ImageField(upload_to='photos/', blank=True, null=True) 
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    # ... keep the rest of the fields exactly the same
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    collections = models.ManyToManyField(Collection, related_name='photos', blank=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Photo by {self.uploader.username}"

# 4. SOCIAL INTERACTIONS
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='liked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'photo') 

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username} on {self.photo.title}"

# 5. MESSAGING SYSTEM
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat ID: {self.id}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']