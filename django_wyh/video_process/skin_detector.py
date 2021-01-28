import os
from os.path import splitext, basename
import cv2
import numpy as np
import torch
import torchvision.transforms as standard_transforms
from PIL import Image
from torch.autograd import Variable
import segmentation_models_pytorch as smp


def image_to_tensor(cv2_image):
    if len(cv2_image.shape) > 2:
        cv2_image = np.transpose(cv2_image, (2, 0, 1))  # color image
    cv2_image = cv2_image.astype(np.float32)
    image_tensor = torch.tensor(cv2_image, dtype=torch.float)
    image_tensor = image_tensor / 255.
    return image_tensor

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class SkinDetector(metaclass=Singleton):

    def __init__(self, input_size=64, resume_file="resume_path", device="cpu"):
        self.device = device
        self.input_size = input_size
        self.model = smp.FPN(
            encoder_name='se_resnext50_32x4d',
            encoder_weights='imagenet',
            classes=1,
            activation='sigmoid',
        )
        self.model.to(device)
        print("===> Resuming from checkpoint.")
        assert os.path.isfile(resume_file), 'Error: no checkpoint found!'
        print("=> loading checkpoint '{}'".format(resume_file))
        checkpoint = torch.load(resume_file, map_location=torch.device(device))
        self.model.load_state_dict(checkpoint['state_dict'])
        self.input_transform = standard_transforms.Compose([
            standard_transforms.Resize(
                (input_size, input_size), interpolation=Image.NEAREST),
            standard_transforms.ToTensor(),
        ])

    def skin_mask(self, cv2_src_image):
        with torch.no_grad():
            image = cv2.cvtColor(cv2_src_image, cv2.COLOR_BGR2RGB)
            orig_shape = image.shape
            image = cv2.resize(
                image, (self.input_size, self.input_size), interpolation=cv2.INTER_AREA)
            image_tensor = image_to_tensor(image)
            image_tensor = image_tensor.unsqueeze(0).to(self.device)
            image_tensor = Variable(image_tensor)
            predicted = self.model(image_tensor)
            npimg = torch.squeeze(predicted).detach().cpu().numpy()
            rescaled = (255.0 * npimg).astype(np.uint8)

            cv2_mask = np.array(rescaled)
            height, width, _ = orig_shape
            cv2_mask = cv2.resize(cv2_mask, (width, height))

            return cv2_mask
