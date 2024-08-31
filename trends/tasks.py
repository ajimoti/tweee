# from apscheduler.schedulers.background import BackgroundScheduler
from trends.services import TwitterService, OpenAIService, TrendsService
from celery import shared_task
from django.core.cache import cache


@shared_task
def process():
    lock_id = "process_task_lock"
    acquire_lock = lambda: cache.add(lock_id, "true", 60*5)  # 5 minute timeout
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            twitter_service = TwitterService()
            openai_service = OpenAIService()
            trends_service = TrendsService(twitter_service, openai_service)
            
            print("Processing trends")
            trends_service.process_trends()
            
            print("Posting trend tweets")
            trends_service.post_trend_tweet()
        finally:
            release_lock()
    else:
        print("Task already running")
