from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index api'),
    path('alive', views.AliveAPI.as_view(), name='alive api'),
    path('stats', views.StatsAPI.as_view(), name='stats api'),
    path('start_video', views.StartVideoAPI.as_view(), name='start api'),
    path('stop_video', views.StopVideoAPI.as_view(), name='stop api'),
    path('users', views.UserListAPI.as_view(), name='users api'),
    path('cameras', views.CameraListAPI.as_view(), name='cameras api'),
    path('videos', views.VideoListAPI.as_view(), name='videos api'),
    path('download_video', views.VideoDownloadAPI.as_view(), name='download video api'),
]