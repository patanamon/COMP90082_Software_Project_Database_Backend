from django.db import models


# Create your models here.


class StudentCommitCounts(models.Model):
    
    student_name = models.CharField(max_length=256, null=False)
    relation_id = models.CharField(max_length=256, null=True)
    commit_counts = models.CharField(max_length=256, null=False)
    space_key = models.CharField(max_length=256, null=True)

    class Meta:
        db_table = 'student_commit_counts'


class GitCommitCounts(models.Model):
    # student_name = models.CharField(max_length=256, null=False)
    space_key = models.CharField(max_length=256, null=False)
    commit_counts = models.CharField(max_length=256, null=False)
    query_date = models.IntegerField(null=False)

    class Meta:
        db_table = 'git_commit_counts'

class GitMetrics(models.Model):
    space_key = models.CharField(max_length=256, null=False)
    file_count = models.IntegerField(null=False)
    class_count = models.IntegerField(null=False)
    function_count = models.IntegerField(null=False)
    code_lines_count = models.IntegerField(null=False)
    declarative_lines_count = models.IntegerField(null=False)
    executable_lines_count = models.IntegerField(null=False)
    comment_lines_count = models.IntegerField(null=False)
    comment_to_code_ratio = models.FloatField(null=False)

    class Meta:
        db_table = 'git_metrics'
