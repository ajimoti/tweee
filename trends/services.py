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

    def split_into_tweets(self, text, max_length=270):
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_length:  # +1 for space
                current_chunk.append(word)
                current_length += len(word) + 1
            else:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

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

    def post_tweet_thread(self, tweet_texts, in_reply_to_id=None):
        try:
            # if tweet_texts is a string, convert it to a list
            if isinstance(tweet_texts, str):
                if len(tweet_texts) <= 280:
                    response = self.client.create_tweet(text=tweet_texts, in_reply_to_tweet_id=in_reply_to_id)
                    return response
                else:
                    text_list = self.split_into_tweets(tweet_texts)
            elif isinstance(tweet_texts, list):
                text_list = tweet_texts
            else:
                raise ValueError("Invalid tweet_texts type")
            
            previous_tweet_id = in_reply_to_id
            total_tweets = len(text_list)
            
            for index, text in enumerate(text_list, start=1):
                # Add numbering to each tweet
                numbered_text = f"({index}/{total_tweets}) {text}"
                
                # Ensure the tweet doesn't exceed 280 characters
                if len(numbered_text) > 280:
                    numbered_text = numbered_text[:277] + "..."
                
                if previous_tweet_id:
                    response = self.client.create_tweet(text=numbered_text, in_reply_to_tweet_id=previous_tweet_id)
                else:
                    response = self.client.create_tweet(text=numbered_text)
                
                previous_tweet_id = response.data['id']
                logger.info(f"Posted tweet {index}/{total_tweets} in thread: {numbered_text}")
            
            return response  # Return the response of the last tweet in the thread
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
            f"""Summarize the context provided in a way that is easy to understand as a tweet.
            Topic: {trend} Headlines: {texts}"""
        )
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a Gen Z influencer skilled in summarizing trending topics and generating a tweet that summarizes the reason why the topic is trending based on the provided article headlines. 
                        Keep it concise and strictly under 150 characters, use casual language 
                        Dont include unnecessary hashtags, Do NOT include any emojis.
                        You must keep it under 150 characters:""",
                },
                {"role": "user", "content": prompt},
            ],
        )
        summary = completion.choices[0].message.content.strip('"')
        # if len(summary) > 250:
        #     raise ValueError(f"Summary is too long for {trend}")

        return prompt, summary

    def generate_tweet(self, trend, context, category):
        prompt = self.select_prompt(category)
        # prompt += f"""You are a popular Twitter influencer known for your {category} tweets. 
        #           Craft a tweet about '{trend}' based on the following context. 
        #           Make sure to keep it under 250 characters, use casual language, 
        #           and sound like a Gen Z influencer. 
        #           Don't include unnecessary hashtags, Don't include emojis unless it's common for the trend.
        #           Use slang and idiomatic expressions where appropriate.
        #           Context: "{context}"
        #           Tweet:"""

        full_prompt = prompt
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a Gen Z influencer known for your viral {category} tweets.
                        Craft a tweet about '{trend}' based on the following context. 
                        Make sure to keep it under 150 characters, use casual language, 
                        and sound like a Gen Z influencer. 
                        Don't include unnecessary hashtags, Don't include emojis unless it's common for the trend.
                        Use slang and idiomatic expressions where appropriate.
                        Context: "{context}"
                    """,
                },
                {"role": "user", "content": full_prompt},
            ],
        )
        tweet = response.choices[0].message.content.strip()
        return full_prompt, tweet

    def select_prompt(self, category):
        prompts = categorized_prompts.get(category, categorized_prompts["general"])

        return random.choice(prompts)


class TrendsService:
    def __init__(self, twitter_service_class, openai_service_class):
        self._twitter_service = None
        self._openai_service = None
        self._twitter_service_class = twitter_service_class
        self._openai_service_class = openai_service_class

    @property
    def twitter_service(self):
        if self._twitter_service is None:
            self._twitter_service = self._twitter_service_class()
        return self._twitter_service

    @property
    def openai_service(self):
        if self._openai_service is None:
            self._openai_service = self._openai_service_class()
        return self._openai_service

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
        batch_size = 10  # Adjust based on your needs

        for i in range(0, len(trends), batch_size):
            batch = trends[i:i+batch_size]
            self.process_trend_batch(batch)

    def process_trend_batch(self, trends):
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
            prompt, tweet_text = self.openai_service.generate_tweet(
                trend_name, context, category
            )
            GeneratedTweet.objects.create(
                trend=trend,
                tweet_text=tweet_text,
                for_account=Account.DOPESHI,
                prompt=prompt
            )
            logger.info(f"Generated tweet for trend: {trend_name}")

            # Generate "why is trending" tweet
            summary_prompt, summary = self.openai_service.summarize_for_tweet(trend_name, context)
            GeneratedTweet.objects.create(
                trend=trend,
                tweet_text=summary,
                for_account=Account.WHY_TRENDING,
                prompt=summary_prompt
            )
            logger.info(f"Generated tweet summary for trend: {trend_name}")

    def post_trend_tweet(self):
        """Post a tweet for a trend on all accounts"""

        for account in Account.choices:
            account_value = account[0]
            
            if account_value in settings.PAUSE_ACCOUNT:
                continue
            
            print(f"Posting tweet for account: {account_value}")
            tweet = GeneratedTweet.objects.filter(
                posted_at__isnull=True, for_account=account_value
            ).select_related("trend").order_by("created_at").first()
            
            if tweet:
                self.post_tweet(tweet, account_value)
                
    def process_latest_trend(self):
        trends = self.get_google_trends()
        print(f"trends: {trends}")
        
        for trend_name in trends: 
            if Trend.objects.filter(name=trend_name).exists():
                logger.info(f"Trend already exists: {trend_name}")
                continue
            
            context = self.get_trend_context(trend_name)
            category = self.openai_service.categorize_tweet(context)
            trend, created = Trend.objects.get_or_create(
                name=trend_name, defaults={"context": context}
            )
            
            if not created and trend.created_at > timezone.now() - timedelta(days=1):
                """Skip trends that were created in the last 24 hours"""
                continue
            prompt, tweet_text = self.openai_service.generate_tweet(
                trend, context, category
            )
            GeneratedTweet.objects.create(
                trend=trend,
                tweet_text=tweet_text,
                for_account=Account.DOPESHI,
                prompt=prompt
            )
            
            summary_prompt, summary = self.openai_service.summarize_for_tweet(trend, context)
            GeneratedTweet.objects.create(
                trend=trend,
                tweet_text=summary,
                for_account=Account.WHY_TRENDING,
                prompt=summary_prompt
            )
            
            """Since we only want to process the first trend, we can break the loop after processing one trend"""
            
            break
            

    def post_tweet(self, tweet, account_value):
        tweet_text = tweet.tweet_text
        # if account_value == Account.WHY_TRENDING:
        #     tweet_text = tweet_text[:277] + "..." if len(tweet_text) > 280 else tweet_text
        
        twitter_service = self.twitter_service.with_account(account_value)
        response = twitter_service.post_tweet_thread(tweet_text)

        if response:
            tweet.tweet_id = response.data['id']
            tweet.posted_at = timezone.now()
            tweet.save()
            logger.info(f"Posted tweet for trend: {tweet.trend.name}")
            
            # if account_value == Account.WHY_TRENDING:
            #     twitter_service.post_tweet_thread(tweet.trend.context, in_reply_to_id=tweet.tweet_id)
            #     logger.info(f"Posted trend context thread: {tweet.trend.name}")
        else:
            logger.error(f"Failed to post tweet thread for trend: {tweet.trend.name}")
