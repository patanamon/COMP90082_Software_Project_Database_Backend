from django.db import models
# Create your models here.


class JiraCountByTime(models.Model):
    id = models.AutoField(primary_key=True)
    space_key = models.CharField(max_length=256, null=False)
    count_time = models.CharField(max_length=256,null=False)
    todo = models.IntegerField( null=False)
    in_progress = models.IntegerField( null=False)
    done = models.IntegerField(null=False)


    class Meta:
        db_table = 'jiraCountByTime'

class IndividualContributions(models.Model):
    id = models.AutoField(primary_key=True)
    space_key = models.CharField(max_length=256, null=False)
    student = models.CharField(max_length=256, null=False)
    done_count = models.IntegerField(null=False)


    class Meta:
        db_table = 'individualContributions'


class Urlconfig(models.Model):
    id = models.AutoField(primary_key=True)
    space_key = models.CharField(max_length=256, null=False)
    jira_url = models.CharField(max_length=256, null=False)
    git_url = models.CharField(max_length=256, null=False)


    class Meta:
        db_table = 'url_config'

