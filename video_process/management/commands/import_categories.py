from django.core.management.base import BaseCommand
from video_process.models import Category
from video_process.wash_hands_classifier3D import classes


class Command(BaseCommand):
    help = 'info'
    

    def handle(self, *args, **options):
        # classes = ['00-other', '01-applicare-sapone', '02-palmo-palmo', '03-palmo-dorso',
        #          '04-palmo-palmo-dita-incrociate', '05-dita-racchiuse', '06-rotazione-pollice',
        #          '07-dita-su-palmo', '08-bagnare-o-risciacquo', '09-asciugare',
        #          '10-chiusura-rubinetto', '11-lavaggio-generico']
        for i, v in enumerate(classes):
            Category.objects.create(name=v, model_bind=i)
