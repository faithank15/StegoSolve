from django.db import models

class StegImage(models.Model):
    image = models.ImageField(upload_to='images/')
