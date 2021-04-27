from django.db import models


# Create your models here.


class StudentCommitCounts(models.Model):
    student_id = models.CharField(max_length=256, null=False)
    relation_idn = models.CharField(max_length=256, null=False)
    commit_count = models.CharField(max_length=256, null=False)
    space_key = models.CharField(max_length=256, null=False)

    class Meta:
        db_table = 'student_commit_counts'
