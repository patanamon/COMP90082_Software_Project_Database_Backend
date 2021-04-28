from django.db import models


class Coordinator(models.Model):
    # github username for accessing private repositories
    git_username = models.CharField(max_length=256, null=True)
    git_password = models.CharField(max_length=256, null=True)
    # atlassian username and password
    atl_username = models.CharField(max_length=256, null=True)
    atl_password = models.CharField(max_length=256, null=True)
    class Meta:
        db_table = 'coordinator'
