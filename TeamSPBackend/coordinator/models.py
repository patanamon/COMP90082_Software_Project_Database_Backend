from django.db import models


class Coordinator(models.Model):
    coordinator_name = models.CharField(max_length=256, null=False)
    # github username for accessing private repositories
    # git_username = models.CharField(max_length=256, null=False)
    # git_password = models.CharField(max_length=256, null=False)
    # atlassian username and password
    # atl_username = models.CharField(max_length=256, null=False)
    # atl_password = models.CharField(max_length=256, null=False)

    class Meta:
        db_table = 'coordinator'
