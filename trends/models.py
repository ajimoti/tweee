from django.db import models


class Account(models.TextChoices):
    DOPESHI = "dopeshi", "DopeShi"
    WHY_TRENDING = "why_trending", "Why Trending"


class Trend(models.Model):
    name = models.CharField(max_length=255)
    context = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GeneratedTweet(models.Model):
    trend = models.ForeignKey(Trend, on_delete=models.CASCADE)
    tweet_text = models.TextField()
    for_account = models.CharField(
        max_length=20, choices=Account.choices, default=Account.DOPESHI
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    tweet_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tweet for {self.trend.name}"
