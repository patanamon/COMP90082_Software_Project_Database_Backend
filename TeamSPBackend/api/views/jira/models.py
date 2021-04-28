from django.db import models
# Create your models here.


class Urlconfig(models.Model):
    id = models.AutoField(primary_key=True)
    space_key = models.CharField(max_length=256, null=False)
    jira_url = models.CharField(max_length=256, null=False)
    git_url = models.CharField(max_length=256, null=False)


    class Meta:
        db_table = 'url_config'

