from django.db import models
# Create your models here.


class TestJira(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.IntegerField()
    message = models.CharField(max_length=50)


    class Meta:
        db_table = 'jira'

