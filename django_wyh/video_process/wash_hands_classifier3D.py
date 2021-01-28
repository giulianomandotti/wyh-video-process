import torch
from .resnet import resnet50

classes = ["09-asciugare", "00-other", "02-palmo-palmo", "05-dita-racchiuse",
           "01-applicare-sapone", "03-palmo-dorso", "04-palmo-palmo-dita-incrociate",
           "08-bagnare-o-risciacquo", "10-chiusura-rubinetto", "06-rotazione-pollice",
           "07-dita-su-palmo", "11-lavaggio-generico"]


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class WashingHandsClassifier3D(metaclass=Singleton):
    def __init__(self, image_size=112, sample_duration=16,
                 resume_file="resume_path", device='cpu', n_classes=12):
        # resume_file = '/home/superior/datasets-nas/washyourhands/data/models/save_185.pth'

        self.model = resnet50(
            num_classes=n_classes,
            shortcut_type='B',
            sample_size=image_size,
            sample_duration=sample_duration)

        if device == 'cuda':
            self.model = self.model.cuda()
            self.model = torch.nn.DataParallel(self.model, device_ids=None)

        self.model.eval()

        pretrain = torch.load(resume_file, map_location=torch.device(device))
        self.model.load_state_dict(pretrain)

        # print(self.model)

    def predict(self, imgs):
        with torch.no_grad():
            out = self.model(imgs)
            _, pred = out.topk(1, 1, True)
            id_winner = pred.item()
        return id_winner
