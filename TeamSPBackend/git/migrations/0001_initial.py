from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StudentCommitCounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=256)),
                ('relation_id', models.CharField(max_length=256)),
                ('commit_counts', models.CharField(max_length=256)),
                ('space_key', models.CharField(max_length=256)),
            ],
            options={
                'db_table': 'student_commit_counts',
            },
        ),
    ]
