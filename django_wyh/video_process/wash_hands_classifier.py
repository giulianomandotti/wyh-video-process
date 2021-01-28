import os
import subprocess
import cv2
import numpy as np
import torch
from PIL import Image
from torch.autograd import Variable
from torch.nn import functional as F
from torchvision import transforms
from .inception_v3 import inception_v3
from imutils.video import FPS

classes = ['00-other', '01-applicare-sapone', '02-palmo-palmo', '03-palmo-dorso',
                 '04-palmo-palmo-dita-incrociate', '05-dita-racchiuse', '06-rotazione-pollice',
                 '07-dita-su-palmo', '08-bagnare-o-risciacquo', '09-asciugare',
                 '10-chiusura-rubinetto', '11-lavaggio-generico']

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class WashingHandsAnalyzer(metaclass=Singleton):
    def __init__(self, image_size=224, resume_file="resume_path", device='cpu'):
        self.device = device
        # prepare data
        self.input_transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            # transforms.CenterCrop(IMG_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        # load neural model
        self.model = inception_v3(num_classes=len(classes))
        self.model.to(self.device)
        print("===> Resuming from checkpoint.")
        assert os.path.isfile(resume_file), 'Error: no checkpoint found!'
        print("=> loading checkpoint '{}'".format(resume_file))
        checkpoint = torch.load(resume_file, map_location=torch.device(self.device))
        self.model.load_state_dict(checkpoint['state_dict'])
        # hook the feature extractor
        final_conv = 'Mixed_7c'
        self.features_blobs = []
        self.model._modules.get(final_conv).register_forward_hook(self._hook_feature)
        # softmax weights
        params = list(self.model.parameters())
        self.weight_softmax = np.squeeze(params[-2].data.cpu().numpy())

    def _hook_feature(self, module, input, output):
        self.features_blobs.append(output.data.cpu().numpy())

    def classifyImage(self, img_pil):
        id_winner = self.getIdWinnerClass(img_pil)
        return classes[id_winner]

    def getClassActivationMap(self, img_pil):
        id_winner = self.getIdWinnerClass(img_pil)

        CAMs = self._CAM(id_winner)

        # render the CAM and output
        # convert PIL to CV2
        open_cv_image = np.array(img_pil)
        # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        height, width, _ = open_cv_image.shape
        CAM = cv2.resize(CAMs[0], (width, height))
        heatmap = cv2.applyColorMap(CAM, cv2.COLORMAP_JET)
        rendered_CAM = heatmap * 0.3 + open_cv_image * 0.5

        return classes[id_winner], CAM, rendered_CAM

    # generate class activation mapping for the top1 prediction
    def _CAM(self, class_idx):
        # generate the class activation maps upsample to 256x256
        size_upsample = (256, 256)
        bz, nc, h, w = self.features_blobs[0].shape
        output_cam = []
        # for idx in class_idx:
        cam = self.weight_softmax[[class_idx]].dot(self.features_blobs[0].reshape((nc, h * w)))
        cam = cam.reshape(h, w)
        cam = cam - np.min(cam)
        cam_img = cam / np.max(cam)
        cam_img = np.uint8(255 * cam_img)
        output_cam.append(cv2.resize(cam_img, size_upsample))
        return output_cam

    def getIdWinnerClass(self, img_pil):
        # img_pil = Image.open(img_path)
        with torch.no_grad():
            img_tensor = self.input_transform(img_pil)
            img_variable = Variable(img_tensor.unsqueeze(0)).to(self.device)
            logit = self.model(img_variable)
            h_x = F.softmax(logit, dim=1).data.squeeze()
            probs, idx = h_x.sort(0, True)
            # print('prob winner: {:.3f} -> {}'.format(probs[0], classes[idx[0].item()]))
        return idx[0].item()


if __name__ == '__main__':
    render = False
    analyzer = WashingHandsAnalyzer(resume_file='checkpoint/model_best-washyourhands-cropped_frames.pth.tar')
    img_path = '/home/superior/datasets-nas/washyourhands/dataset/frames+crops/test/02-palmo-palmo/20200425_igna_01-1111.jpg'
    src_dir = '/home/superior/datasets-nas/washyourhands/dataset/frames+crops/test/02-palmo-palmo/'
    src_dir = '/home/superior/datasets-nas/washyourhands/dataset/frames+crops/test/04-palmo-palmo-dita-incrociate'
    src_dir = '/home/superior/datasets-nas/washyourhands/dataset/frames+crops/test/06-rotazione-pollice'
    src_dir = '/home/superior/datasets-nas/washyourhands/dataset/frames+crops/test/07-dita-su-palmo'
    if render:
        if os.path.exists('tmp'):
            subprocess.call('rm -rf tmp', shell=True)
        subprocess.call('mkdir tmp', shell=True)

    counts = dict()
    fps = FPS().start()
    for file_name in os.listdir(src_dir):
        img_pil = Image.open(os.path.join(src_dir, file_name))
        if render:
            cls_winnwer, cv2CAM, cv2renderedCAM = analyzer.getClassActivationMap(img_pil)
            cv2.imwrite(os.path.join('tmp', cls_winnwer + '-' + file_name), cv2renderedCAM)
        else:
            cls_winnwer = analyzer.classifyImage(img_pil)
        print(cls_winnwer, '<--', file_name)
        counts[cls_winnwer] = counts.get(cls_winnwer, 0) + 1
        fps.update()

    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    print('Histogram:')
    for i in sorted(counts, key=counts.get):
        print("%d\t'%s'" % (counts[i], i))