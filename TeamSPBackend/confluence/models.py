from django.db import models


# Create your models here.

class MeetingMinutes(models.Model):
    meeting_id = models.IntegerField(primary_key=True)
    meeting_title = models.CharField(max_length=256)
    meeting_link = models.TextField()
    space_key = models.CharField(max_length=256)

    class Meta:
        db_table = 'meeting_minutes'

class UserList(models.Model):

    user_id = models.CharField(max_length=256, null=False)
    user_name = models.CharField(max_length=256, null=False)
    email = models.EmailField(max_length=256, null=False)
    picture = models.CharField(max_length=256, null=False)
    space_key = models.CharField(max_length=256, null=False)

    class Meta:
        db_table = 'user_list'

        
class PageHistory(models.Model):
    page_count = models.IntegerField()
    date = models.IntegerField()
    space_key = models.CharField(max_length=256)

    class Meta:
        db_table = 'page_history'
