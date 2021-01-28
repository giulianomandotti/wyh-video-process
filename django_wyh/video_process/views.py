from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Video, Frame, Category, User, Camera
from . import models_serializers
from django.core.management import call_command
from multiprocessing import Pool
from wsgiref.util import FileWrapper


class IndexView(TemplateView):
    template_name = 'index.html'


class AliveAPI(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        response = {'status': 'ok'}
        return Response(response, status=status.HTTP_200_OK,)


class StatsAPI(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        response = {c.name: 0.0 for c in Category.objects.all()}

        video_id = int(request.data['video_id'])

        frames = Frame.objects.filter(video_id=video_id).all()
        for f in frames:
            response[f.category.name] += 1

        frame_rate = Video.objects.get(pk=video_id).frame_rate
        for k in response.keys():
            response[k] /= frame_rate
        response['frame_processed'] = len(frames)
        response['processing_time'] = len(frames)/frame_rate

        return Response(response, status=status.HTTP_200_OK,)


def start_stream_reader(user_id, camera_id):
    call_command('stream_reader3D', user=user_id, camera=camera_id)


class StartVideoAPI(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        user_id = int(request.data['user_id'])
        camera_id = int(request.data['camera_id'])

        pool = Pool(processes=1)
        result = pool.apply_async(start_stream_reader, [user_id, camera_id])

        return Response("Ok", status=status.HTTP_200_OK)


class StopVideoAPI(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        video_id = int(request.data['video_id'])
        video = Video.objects.get(pk=video_id)
        video.status_item = 'stop requested'
        video.save()

        return Response("Ok", status=status.HTTP_200_OK)


class UserListAPI(generics.ListAPIView):
    queryset = User.objects.all().order_by('name')
    serializer_class = models_serializers.UserSerializer
    permission_classes = []


class CameraListAPI(generics.ListAPIView):
    queryset = Camera.objects.all().order_by('name')
    serializer_class = models_serializers.CameraSerializer
    permission_classes = []


class VideoListAPI(generics.ListAPIView):
    queryset = Video.objects.all().order_by('created_at')
    serializer_class = models_serializers.VideoSerializer
    permission_classes = []
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ("user",)


class VideoDownloadAPI(APIView):
    def get(self, request, *args, **kwargs):
        video_id = int(request.GET.get('video_id'))
        video = Video.objects.get(pk=video_id)
        # file_path = '/home/ignazio/datasets/washyourhands/my_video_splitted/09-asciugare/ignazio_20200705_h10_v0.mp4'
        file_path = 'video_frames/{}/{}_{}.mp4'.format(video.user.id, video.id, video.created_at)
        video_file = open(file_path, 'rb')
        response = HttpResponse(
            FileWrapper(video_file),
            content_type='application/video',
        )
        response['Content-Disposition'] = 'attachment; filename="%s"' % 'video_id-{}_user-{}-{}.mp4'.format(video_id, video.user.id, video.user.name)
        return response
