from django.core.management.base import BaseCommand
from trends.services import TwitterService, OpenAIService, TrendsService


class Command(BaseCommand):
    help = "Post a generated tweet about a trending topic"

    def handle(self, *args, **options):
        twitter_service = TwitterService()
        openai_service = OpenAIService()
        trends_service = TrendsService(twitter_service, openai_service)

        trends_service.process_trends()

        # we will use why_trending twitter client for this part
        # trends_service.post_trend_tweet()
