from django.db import models


# Create your models here.


class StudentCommitCounts(models.Model):
    
    student_name = models.CharField(max_length=256, null=False)
    relation_id = models.CharField(max_length=256, null=True)
    commit_counts = models.CharField(max_length=256, null=False)
    space_key = models.CharField(max_length=256, null=True)

    class Meta:
        db_table = 'student_commit_counts'
