# Generated by Django 5.2.1 on 2025-07-10 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_flix_app', '0009_alter_video_video_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='genre',
            field=models.CharField(max_length=255),
        ),
    ]
