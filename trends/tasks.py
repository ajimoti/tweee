from celery import shared_task
from django.core.cache import cache
from trends.services import TwitterService, OpenAIService, TrendsService

@shared_task
def process():
    lock_id = "process_task_lock"
    acquire_lock = lambda: cache.add(lock_id, "true", 60*5)  # 5 minute timeout
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            trends_service = TrendsService(TwitterService, OpenAIService)
            
            print("Processing trends")
            trends_service.process_trends()
            
            print("Posting trend tweets")
            trends_service.post_trend_tweet()
        finally:
            release_lock()
    else:
        print("Task already running")
