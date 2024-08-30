# from apscheduler.schedulers.background import BackgroundScheduler
from trends.services import TwitterService, OpenAIService, TrendsService
from celery import shared_task


@shared_task
def process():
    twitter_service = TwitterService()
    openai_service = OpenAIService()
    trends_service = TrendsService(twitter_service, openai_service)
    
    print("Processing trends")
    trends_service.process_trends()
    
    print("Posting trend tweets")
    trends_service.post_trend_tweet()
