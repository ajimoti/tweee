from django.core.management.base import BaseCommand
from trends.services import TwitterService, OpenAIService, TrendsService


class Command(BaseCommand):
    help = "Post a generated tweet about a trending topic"

    def handle(self, *args, **options):
        trends_service = TrendsService(TwitterService, OpenAIService)

        trends_service.process_latest_trend()
        # trends_service.process_trends()

        # we will use why_trending twitter client for this part
        trends_service.post_trend_tweet()
