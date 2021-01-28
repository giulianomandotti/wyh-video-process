from .models import Frame, Category
from time import time
from .skin_detector import SkinDetector
from .wash_hands_classifier import WashingHandsAnalyzer
from .wash_hands_classifier3D import WashingHandsClassifier3D
import cv2
import numpy as np
from PIL import Image
import torch
import os
from .spatial_transforms import (Compose, Normalize, Scale, CenterCrop, ToTensor)


def test_gpu_settings():
    use_gpu = torch.cuda.is_available()

    if use_gpu:
        return "cuda"
    else:
        return "cpu"


def crop_with_mask(cv2_image, cv2_mask):
    th_mask = cv2_mask > 128

    # only skin pixel, background white
    only_skin = cv2_image.copy()
    only_skin[cv2_mask == 0] = 255

    # combine mask and image
    (contours, _) = cv2.findContours(cv2_mask,
                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Coordinates of non-black pixels.
    coords = np.argwhere(th_mask)
    if (len(coords) > 0):
        # Bounding box of non-black pixels.
        x0, y0 = coords.min(axis=0)
        # slices are exclusive at the top
        x1, y1 = coords.max(axis=0) + 1
        # crop image
        return True, cv2_image[x0:x1, y0:y1]
    else:
        return False, None


def ai_model_worker(id_video, frame_number, img):
    t_now = time()

    device = test_gpu_settings()
    print('Used device:', device, 'pid:', os.getpid())
    detector = SkinDetector(input_size=256,
                            resume_file="models/skin_model_best_FSD_256.pth.tar",
                            device=device)

    cv2_mask = detector.skin_mask(img)
    is_skin_present, cropped_img = crop_with_mask(img, cv2_mask)

    category_id = Category.objects.get(model_bind=0).id
    if is_skin_present:
        classifier = WashingHandsAnalyzer(
            resume_file="models/model_best-washyourhands-cropped_frames.pth.tar",
            device=device)
        pil_image = Image.fromarray(cropped_img)
        cls_winnwer = classifier.getIdWinnerClass(pil_image)
        # print(cls_winnwer)
        category_id = Category.objects.get(model_bind=cls_winnwer).id

    t_total = time() - t_now

    Frame.objects.create(video_id=id_video,
                         category_id=category_id,
                         number=frame_number,
                         processing_time_ms=t_total)
    return id_video


def ai_model_worker3D(id_video, first_frame_number, imgs):
    t_now = time()

    sample_size = 112
    mean = [114.7748, 107.7354, 99.4750]
    norm_method = Normalize(mean, [1, 1, 1])
    spatial_transform = Compose([
        Scale(sample_size),
        CenterCrop(sample_size),
        ToTensor(1), 
        norm_method
    ])
    spatial_transform.randomize_parameters()
    clip = [spatial_transform(img) for img in imgs]
    clip_tensor = torch.stack(clip, 0).permute(1, 0, 2, 3)
    clip_tensor = clip_tensor.unsqueeze(dim=0)
    
    device = test_gpu_settings()
    print('Used device:', device, 'pid:', os.getpid())
    clip_tensor = clip_tensor.to(device)
    classifier = WashingHandsClassifier3D(
            resume_file="models/resnet50-3D-ep300_state_dict.pth",
            device=device)
    id_winner = classifier.predict(clip_tensor)
    
    category_id = Category.objects.get(model_bind=id_winner).id
    
    t_total = time() - t_now

    for i in range(16):
        frame_number = i + first_frame_number
        Frame.objects.create(video_id=id_video,
                            category_id=category_id,
                            number=frame_number,
                            processing_time_ms=t_total/16.0)
    return id_video