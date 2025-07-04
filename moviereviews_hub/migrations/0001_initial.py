# Generated by Django 5.2.1 on 2025-05-28 00:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('director', models.CharField(max_length=100)),
                ('starring_actors', models.CharField(max_length=200)),
                ('genres', models.CharField(max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('couple_id', models.CharField(max_length=20)),
                ('reviewer', models.CharField(max_length=15)),
                ('rating', models.FloatField()),
                ('rating_justification', models.TextField()),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='moviereviews_hub.movie')),
            ],
        ),
    ]
