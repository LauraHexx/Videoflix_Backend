# Generated by Django 5.2.1 on 2025-06-21 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_flix_app', '0006_userwatchhistory_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='duration',
            field=models.PositiveIntegerField(blank=True, help_text='Duration in seconds', null=True),
        ),
    ]
