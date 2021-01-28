from django.db import models

class User(models.Model):
    name = models.CharField(max_length=200)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '(%d) %s' % (self.id, self.name)
    
class Category(models.Model):
    name = models.CharField(max_length=200)
    model_bind = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '(%d) %s' % (self.id, self.name)

class Camera(models.Model):
    url = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '(%d) %s' % (self.id, self.name)

class Video(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    finish = models.BooleanField(default=False)
    status_item = models.CharField(max_length=200, default="started")
    frame_rate = models.FloatField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '(%d) User: %s' % (self.id, self.user.name)

class Frame(models.Model):
    video = models.ForeignKey(Video, related_name='frames', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    number = models.IntegerField()
    processing_time_ms = models.FloatField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
