#from django.db import models

#from tom_targets.base_models import BaseTarget

class Product(models.Model):
    name = models.CharField(max_length=100)
    # upload_to='products/' means files will be stored in your_project/media/products/
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.name