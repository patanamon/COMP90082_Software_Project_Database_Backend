from django.db import models

# Create your models here.


class UserList(models.Model):

    user_id = models.CharField(max_length=256, null=False)
    user_name = models.CharField(max_length=256, null=False)
    email = models.EmailField(max_length=256, null=False)
    picture = models.CharField(max_length=256, null=False)
    space_key = models.CharField(max_length=256, null=False)

    class Meta:
        db_table = 'user_list'
