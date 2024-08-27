from django.db import models
from django.utils import timezone


class Tweet(models.Model):
    tweet_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
