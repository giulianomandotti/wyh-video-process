from django.core.management.base import BaseCommand
from video_process.models import Video, Camera
import django_rq
from video_process.ai_model import ai_model_worker
import cv2
import os
from time import time
import subprocess
import shutil

class Command(BaseCommand):
    help = 'info'
    image_size = 256
    max_video_number_per_user = 7

    def _to_stop(self, video):
        video.refresh_from_db()
        if video.status_item == 'stop requested':
            video.status_item = 'stopped'
            video.save()
            return True
        return False

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='Id of user',
        )
        parser.add_argument(
            '--camera',
            type=int,
            help='Id of camera',
        )

    def handle(self, *args, **options):
        # get queue
        queue = django_rq.get_queue('default')

        camera_id = options['camera']
        camera = Camera.objects.get(pk=camera_id)
        actual_video = Video.objects.create(
            user_id=options['user'], 
            camera_id=camera_id,
            frame_rate=30)

        # create video folder
        dst_dir = 'video_frames/' + str(options['user']) + '/' + str(actual_video.id)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        video_url = camera.url
        video_capture = cv2.VideoCapture(video_url)

        num_frames = 0
        start_fps = time()
        while video_capture.isOpened():
            ret, frame1 = video_capture.read()
            if ret == True:
                print('\rtest %d' % (num_frames), end="")

                # resize image
                frame_height, frame_width, channels = frame1.shape
                scale = float(Command.image_size) / \
                    min(frame_height, frame_width)
                width_resized = int(frame_width * scale)
                height_resized = int(frame_height * scale)
                frame1 = cv2.resize(frame1, (width_resized, height_resized))

                # write image
                cv2.imwrite(os.path.join(dst_dir, '%07d.jpg' %
                                         num_frames), frame1)

                # enqueue
                # ai_model_worker(id_video=actual_video.id,
                #                frame_number=num_frames,
                #                img=frame1,)
                queue.enqueue(ai_model_worker,
                          id_video=actual_video.id,
                          frame_number=num_frames,
                          img=frame1,
                          at_front=True)
                num_frames += 1
                if self._to_stop(actual_video):
                    break
            else:
                break
        tot_time = time() - start_fps
        print('\ntime:', num_frames, 'fps', num_frames/tot_time)

        video_capture.release()

        # TODO crea video a db e incoda frame con numero progressivo
        # use queue
        # for i in range(5):
        #     queue.enqueue(ai_model_worker,
        #                   id_video=actual_video.id,
        #                   frame_number=i,
        #                   img=None,
        #                   at_front=True)

        # folder: dst_dir
        # expression: '%07d.jpg'
        # genera video
        frames_path = dst_dir + '/%07d.jpg'
        video_name = dst_dir + '_' + str(actual_video.created_at)  + '.mp4'
        
        cmd = 'ffmpeg -r {} -i {} -c:v libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" "{}"'.format(actual_video.frame_rate, frames_path, video_name)
        print(cmd)
        subprocess.call(cmd, shell=True)
        
        # rimuovi folder
        shutil.rmtree(dst_dir)
        
        # se i video sono più di X rimuovi il più vecchio
        video_base_path = os.path.dirname(dst_dir)
        files = os.listdir(video_base_path)
        if len(files) > Command.max_video_number_per_user:
            files.sort(key=lambda x: x.split('_')[-1])
            old_file_path = os.path.join(video_base_path, files[0])
            print('remove file: ', old_file_path)
            os.remove(old_file_path)
            
        
        actual_video.finish = True
        actual_video.save()

        self.stdout.write('test %d' % (num_frames))
