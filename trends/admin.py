from django.contrib import admin
from .models import GeneratedTweet, Trend

# Register your models here.
@admin.register(GeneratedTweet)
class GeneratedTweetAdmin(admin.ModelAdmin):
    list_display = ("trend", "tweet_text", "for_account", "posted_at", "tweet_id", "prompt")
    list_filter = ("for_account", "posted_at")
    search_fields = ("trend__name", "tweet_text")


@admin.register(Trend)
class TrendAdmin(admin.ModelAdmin):
    list_display = ("name", "context", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "context")
