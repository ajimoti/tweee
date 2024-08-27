import random
import logging
import requests
import praw
from googlesearch import search
from django.utils import timezone
from tweepy import Client, errors as tweepy_errors
from openai import OpenAI
from trends.models import Account, Trend, GeneratedTweet
from pytrends.request import TrendReq
from django.conf import settings
from .prompts import categorized_prompts
from bs4 import BeautifulSoup
from datetime import timedelta

# from twitter_bot_project.settings import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

logger = logging.getLogger(__name__)


class TwitterService:
    def __init__(self, client=None, account=None):
        self.client = None

        if account:
            self.client = self.get_account_client(account)

        if client:
            """If a client is provided, use it. Overrides the account client"""
            self.client = client

        if not self.client:
            self.client = self.get_account_client(Account.DOPESHI)

    def get_account_client(self, account):
        if account == Account.DOPESHI:
            return Client(
                bearer_token=settings.DOPESHI_TWITTER_BEARER_TOKEN,
                consumer_key=settings.DOPESHI_TWITTER_API_KEY,
                consumer_secret=settings.DOPESHI_TWITTER_API_SECRET,
                access_token=settings.DOPESHI_TWITTER_ACCESS_TOKEN,
                access_token_secret=settings.DOPESHI_TWITTER_ACCESS_SECRET,
            )
        elif account == Account.WHY_TRENDING:
            return Client(
                bearer_token=settings.WHY_TRENDING_TWITTER_BEARER_TOKEN,
                consumer_key=settings.WHY_TRENDING_TWITTER_API_KEY,
                consumer_secret=settings.WHY_TRENDING_TWITTER_API_SECRET,
                access_token=settings.WHY_TRENDING_TWITTER_ACCESS_TOKEN,
                access_token_secret=settings.WHY_TRENDING_TWITTER_ACCESS_SECRET,
            )

        raise ValueError(f"Invalid account: {account}")

    def with_account(self, account):
        """Chainable method to set the account client"""
        self.client = self.get_account_client(account)
        return self

    def post_tweet(self, text):
        try:
            response = self.client.create_tweet(text=text)
            logger.info(f"Posted tweet: {text}")
            return response
        except tweepy_errors.Forbidden as e:
            logger.error(f"Twitter error: {e}")
            return None


class OpenAIService:
    def __init__(self):
        self.client = OpenAI()

    def categorize_tweet(self, text):
        categories = ", ".join(categorized_prompts.keys())
        categorization_prompt = (
            f"Categorize the following tweet into one of these categories: {categories}"
            f'Tweet: "{text}"\n\nCategory:'
        )
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a popular Twitter influencer skilled in writing viral content.",
                },
                {"role": "user", "content": categorization_prompt},
            ],
        )
        category = response.choices[0].message.content.strip().lower()
        return category

    def summarize_trend(self, trend, texts):
        prompt = (
            f"Summarize why the following topic is trending based on the provided tweets separated by |||:\n\n"
            f"Topic: {trend}\n\nHeadlines: {texts}\n\nSummary:"
        )
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are skilled in summarizing trending topics based on article headlines.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        summary = completion.choices[0].message.content.strip()
        return summary

    def summarize_for_tweet(self, trend, texts):
        prompt = (
            f"""You are a popular Twitter influencer known for your summarizing trending topics. 
                Summarize the texts provided in a way that is easy to understand as a tweet. 
                Keep it concise and strictly under 250 characters, use casual language 
                Don't include unnecessary hashtags, Do NOT include any emojis.
                You must keep it under 251 characters:\n\n"""
            f"Topic: {trend}\n\nTweets: {texts}\n\nSummary:"
        )
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Gen Z influencer skilled in summarizing trending topics based and generating tweets based on the context.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        summary = completion.choices[0].message.content.strip('"')
        if len(summary) > 250:
            raise ValueError(f"Summary is too long for {trend}")

        return summary

    def generate_tweet(self, trend, context, category):
        prompt = self.select_prompt(category)
        prompt += f"""You are a popular Twitter influencer known for your {category} tweets. Craft a tweet about '{trend}' based on the following context. 
                 Make sure to keep it under 250 characters, use casual language, and sound like a Gen Z influencer. 
                 Don't include unnecessary hashtags, Don't include emojis unless it's common for the trend.
                 Context: "{context}"
                 Tweet:"""

        full_prompt = prompt
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Gen Z influencer known for your viral tweets.",
                },
                {"role": "user", "content": full_prompt},
            ],
        )
        tweet = response.choices[0].message.content.strip()
        return tweet

    def select_prompt(self, category):
        prompts = categorized_prompts.get(category, categorized_prompts["general"])

        return random.choice(prompts)


class TrendsService:
    def __init__(self, twitter_service, openai_service):
        self.twitter_service = twitter_service
        self.openai_service = openai_service

    def get_google_trends(self, use_realtime=False):
        pytrends = TrendReq()

        if use_realtime:
            trending_searches = pytrends.realtime_trending_searches(pn="US")
            trends = trending_searches["title"].tolist()
        else:
            trending_searches = pytrends.trending_searches()
            trends = trending_searches[0].tolist()

        return trends

    def get_google_context(self, trend):
        """Get context from google trends"""

        try:
            pytrends = TrendReq()
            pytrends.build_payload(
                [trend], cat=0, timeframe="now 1-d", geo="", gprop=""
            )
            related_queries = pytrends.related_queries()

            context = (
                related_queries[trend]["top"]["query"].tolist()
                if related_queries[trend]["top"] is not None
                else []
            )
            print(f"Google related queries: {context}")
            return context
        except Exception as e:
            print(f"An error occurred while fetching google context. Error: {e}")

    def get_news_context(self, trend):
        """Get context from News"""
        query = trend.replace(" ", "+")
        url = f"https://news.google.com/search?q={query}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        headlines = []
        for item in soup.select("article a"):
            headlines.append(item.get_text())

        if len(headlines):
            print(f"found {len(headlines)} news headlines")

        return headlines

    def get_reddit_context(self, trend):
        reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )

        subreddit = reddit.subreddit("all")
        posts = subreddit.search(trend, limit=10)

        context = []
        for post in posts:
            context.append(post.title)

        return context

    def get_search_context(self, trend):
        query = trend
        search_results = search(query, num_results=10)
        results = []
        for link in search_results:
            results.append(link)
        return search_results

    def get_trend_context(self, trend):
        print(f"trend: {trend}")
        # google_context = self.get_google_context(trend)
        news_context = self.get_news_context(trend)
        # reddit_context = self.get_reddit_context(trend)
        # search_context = self.get_search_context(trend)

        # Combine all contexts
        all_contexts = {
            # "google": google_context,
            "news": news_context,
            # "reddit": reddit_context,
            # "search": search_context
        }

        concatenated_contexts = ""
        for provider, contexts in all_contexts.items():
            concatenated_contexts += " ||| ".join(contexts)

        summarized_trend = self.openai_service.summarize_trend(
            trend, concatenated_contexts
        )

        return summarized_trend

    # def get_trend_context(self, trend):
    #     tweets = self.twitter_service.client.search_recent_tweets(query=trend, max_results=10)
    #     tweets_text = " ||| ".join([tweet.text for tweet in tweets.data])
    #     context = self.openai_service.summarize_trend(trend, tweets_text)
    #     return context

    def process_trends(self):
        trends = self.get_google_trends()

        for trend_name in trends:
            context = self.get_trend_context(trend_name)
            trend, created = Trend.objects.get_or_create(
                name=trend_name, defaults={"context": context}
            )
            if created:
                logger.info(f"New trend added: {trend_name}")

            if not created and trend.created_at > timezone.now() - timedelta(days=1):
                """Skip trends that were created in the last 24 hours"""
                continue

            category = self.openai_service.categorize_tweet(context)
            tweet_text = self.openai_service.generate_tweet(
                trend_name, context, category
            )
            GeneratedTweet.objects.create(
                trend=trend, tweet_text=tweet_text, for_account=Account.DOPESHI
            )
            logger.info(f"Generated tweet for trend: {trend_name}")

            # Generate "why is trending" tweet
            summary = self.openai_service.summarize_for_tweet(trend_name, context)
            GeneratedTweet.objects.create(
                trend=trend, tweet_text=summary, for_account=Account.WHY_TRENDING
            )
            logger.info(f"Generated tweet summary for trend: {trend_name}")

    def post_trend_tweet(self):
        """Post a tweet for a trend on all accounts"""

        for account in Account.choices:
            if account == Account.DOPESHI:
                continue

            account_value = account[0]
            print(f"Posting tweet for account: {account_value}")
            tweet = (
                GeneratedTweet.objects.filter(
                    posted_at__isnull=True, for_account=account_value
                )
                .order_by("created_at")
                .first()
            )
            if tweet:
                response = self.twitter_service.with_account(account_value).post_tweet(
                    tweet.tweet_text
                )

                if response:
                    tweet.tweet_id = response.data["id"]
                    tweet.posted_at = timezone.now()
                    tweet.save()
                    logger.info(f"Tweet posted for trend: {tweet.trend.name}")
            else:
                logger.error(f"Failed to post tweet for trend: {tweet.trend.name}")
