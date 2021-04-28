from django.db import models


# Create your models here.


class PageHistory(models.Model):
    page_count = models.IntegerField()
    date = models.IntegerField()
    space_key = models.CharField(max_length=256)

    class Meta:
        db_table = 'page_history'
