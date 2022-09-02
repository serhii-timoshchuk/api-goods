from django.db import models
from django.conf import settings
from django.utils import timezone
import os


def gallery_path(instance, filename):
    return os.path.join('gallery', str(instance.product.id), filename)


class Author(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, blank=False)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='user')
    price = models.DecimalField(max_digits=11,
                                decimal_places=2,
                                default=0)
    createdon = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(Author,
                               on_delete=models.SET_NULL,
                               null=True, blank=True)

    def __str__(self):
        return self.name


class Gallery(models.Model):
    image = models.ImageField(upload_to=gallery_path, null=False, blank=False)
    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE)

    def __str__(self):
        return self.image.name
