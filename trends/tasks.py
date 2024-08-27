from apscheduler.schedulers.background import BackgroundScheduler
from trends.services import TwitterService, OpenAIService, TrendsService


def start_trending_scheduler():
    scheduler = BackgroundScheduler()
    twitter_service = TwitterService()
    openai_service = OpenAIService()
    trends_service = TrendsService(twitter_service, openai_service)

    scheduler.add_job(trends_service.post_trend_tweet, "interval", minutes=15)
    scheduler.start()
