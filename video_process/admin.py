from django.contrib import admin
from .models import User, Category, Video, Frame, Camera

class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']    
    
admin.site.register(User, UserAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'model_bind']
    search_fields = ['name']   
admin.site.register(Category, CategoryAdmin)

class CameraAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'url']
    search_fields = ['name']
admin.site.register(Camera, CameraAdmin)


class VideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'camera', 'status_item']
    search_fields = ['status_item']
admin.site.register(Video, VideoAdmin)

class FrameAdmin(admin.ModelAdmin):
    list_display = ['id', 'video', 'category', 'processing_time_ms']
    list_filter = ['category', 'video']
admin.site.register(Frame, FrameAdmin)

