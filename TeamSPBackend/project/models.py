from django.db import models


class ProjectCoordinatorRelation(models.Model):
    coordinator_id = models.IntegerField(null=False)
    space_key = models.CharField(max_length=256, null=False)
    git_url = models.CharField(max_length=256, null=False)
    jira_project = models.CharField(max_length=256, null=False)
    git_username = models.CharField(max_length=256, null=False,default="")
    git_password = models.CharField(max_length=256, null=False,default="")

    class Meta:
        db_table = 'project_coordinator_relation'
