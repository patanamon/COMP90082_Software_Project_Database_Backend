from django.db import models


# Create your models here.


class PageHistory(models.Model):
    page_count = models.IntegerField(null=False)
    date = models.IntegerField(null=False)
    space_key = models.CharField(max_length=256, null=False)

    class Meta:
        db_table = 'page_history'
