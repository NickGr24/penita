from django.db import models
from django.utils.text import slugify

class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='news/', height_field=None, width_field=None, max_length=None)
    slug = models.SlugField()

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Noutate'
        verbose_name_plural = 'Noutăți'
