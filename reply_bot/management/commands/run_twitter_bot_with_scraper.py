import random
import openai
import twikit
from django.core.management.base import BaseCommand
from django.utils import timezone
from reply_bot.models import Tweet
from pytrends.request import TrendReq
from apscheduler.schedulers.background import BackgroundScheduler
from twikit.client.client import Client


class Command(BaseCommand):
    help = "Run the Twitter bot"

    def handle(self, *args, **options):

        # Initialize Twikit API
        api = twikit.API()

        # OpenAI API key
        openai.api_key = "YOUR_OPENAI_API_KEY"

        # List of prompts
        prompts = [
            "You're a clever and engaging Twitter influencer. Respond to this tweet in a way that sparks conversation, uses humor, and is relatable to current events:",
            "As a thought-provoking Twitter personality, reply to this tweet with a controversial opinion that drives engagement. Keep it within Twitter guidelines:",
        ]

        original_tweet_prompts = [
            "You're a witty and engaging Twitter user. Craft a tweet about this trending topic that will drive interaction:",
            "As a thought-provoking Twitter personality, create a tweet about this trending topic that encourages discussion. Keep it within Twitter guidelines:",
        ]

        def generate_reply(tweet_text, model="text-davinci-003"):
            prompt = random.choice(prompts)
            prompt += f'\n\nTweet: "{tweet_text}"\n\nReply:'
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=60,
                n=1,
                stop=None,
                temperature=0.7,
            )
            reply = response.choices[0].text.strip()
            return reply

        def generate_original_tweet(trend, model="text-davinci-003"):
            prompt = random.choice(original_tweet_prompts)
            prompt += f'\n\nTrending Topic: "{trend}"\n\nTweet:'
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=60,
                n=1,
                stop=None,
                temperature=0.7,
            )
            tweet = response.choices[0].text.strip()
            return tweet

        def get_twitter_trends():
            trends_result = api.get_trends_place(id=1)  # WOEID 1 for global trends
            trends = [trend["name"] for trend in trends_result[0]["trends"]]
            return trends

        def get_google_trends():
            pytrends = TrendReq()
            trending_searches = pytrends.trending_searches()
            trends = trending_searches[0].tolist()
            return trends

        def get_combined_trends():
            twitter_trends = get_twitter_trends()
            google_trends = get_google_trends()
            combined_trends = list(set(twitter_trends + google_trends))
            return combined_trends

        class MyStreamListener(twikit.StreamListener):
            def __init__(self, api):
                super().__init__()
                self.api = api
                self.trends = get_combined_trends()
                self.last_trend_fetch = timezone.now()

            def on_status(self, status):
                if not hasattr(status, "retweeted_status"):  # Ignore retweets
                    tweet_text = status.text
                    user_screen_name = status.user.screen_name
                    tweet_id = status.id

                    # Avoid self-reply
                    if user_screen_name == "YOUR_TWITTER_HANDLE":
                        return

                    # Check if daily limit is reached
                    today = timezone.now().date()
                    daily_tweets = Tweet.objects.filter(created_at__date=today).count()

                    if daily_tweets >= 40:
                        return

                    # Refresh trends every hour
                    if (timezone.now() - self.last_trend_fetch).total_seconds() > 3600:
                        self.trends = get_combined_trends()
                        self.last_trend_fetch = timezone.now()

                    # Ensure the bot only replies to tweets that meet certain criteria
                    if not self.should_reply(status):
                        return

                    # Generate a reply using OpenAI
                    reply_text = generate_reply(tweet_text)

                    # Construct the URL of the tweet to quote reply
                    tweet_url = (
                        f"https://twitter.com/{user_screen_name}/status/{tweet_id}"
                    )

                    # Post the quote reply
                    self.api.update_status(status=f"{reply_text} {tweet_url}")

                    # Log the tweet in the database
                    Tweet.objects.create(tweet_id=tweet_id)

                    print(
                        f"Quote replied to @{user_screen_name}: {reply_text} {tweet_url}"
                    )

            def should_reply(self, status):
                # Ensure the user has more than 10,000 followers
                return status.user.followers_count >= 10000

            def on_error(self, status_code):
                if status_code == 420:
                    # Returning False in on_error disconnects the stream
                    return False

        def start_stream(api, listener):
            stream = twikit.Stream(api.auth, listener)
            stream.filter(track=["Kamala Harris", "Megan Thee Stallion", "debate"])

        def post_original_tweet(api):
            # Refresh trends every hour
            trends = get_combined_trends()

            # Generate an original tweet using OpenAI based on a trending topic
            trend = random.choice(trends)
            tweet_text = generate_original_tweet(trend)

            # Post the tweet
            api.update_status(status=tweet_text)
            print(f"Original tweet posted: {tweet_text}")

        listener = MyStreamListener(api)
        scheduler = BackgroundScheduler()
        scheduler.add_job(start_stream, "interval", minutes=1, args=[api, listener])
        scheduler.add_job(post_original_tweet, "interval", hours=1, args=[api])
        scheduler.start()
        start_stream(api, listener)
