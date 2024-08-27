import random
import tweepy

# import openai
from openai import OpenAI
from django.core.management.base import BaseCommand
from django.utils import timezone
from reply_bot.models import Tweet
from pytrends.request import TrendReq
import time
import schedule
import json
from twitter_bot_project.settings import (
    DOPESHI_TWITTER_BEARER_TOKEN,
    DOPESHI_TWITTER_API_KEY,
    DOPESHI_TWITTER_API_SECRET,
    DOPESHI_TWITTER_ACCESS_TOKEN,
    DOPESHI_TWITTER_ACCESS_SECRET,
    DOPESHI_TWITTER_CLIENT_ID,
    DOPESHI_TWITTER_CLIENT_SECRET,
)


class Command(BaseCommand):
    help = "Run the Twitter bot"

    def handle(self, *args, **options):
        # Twitter API authentication
        # auth = tweepy.OAuthHandler(DOPESHI_TWITTER_API_KEY, DOPESHI_TWITTER_API_SECRET)
        # auth.set_access_token(DOPESHI_TWITTER_ACCESS_TOKEN, DOPESHI_TWITTER_ACCESS_SECRET)
        # api = tweepy.API(auth)

        dopeshi_client = tweepy.Client(
            bearer_token=DOPESHI_TWITTER_BEARER_TOKEN,
            consumer_key=DOPESHI_TWITTER_API_KEY,
            consumer_secret=DOPESHI_TWITTER_API_SECRET,
            access_token=DOPESHI_TWITTER_ACCESS_TOKEN,
            access_token_secret=DOPESHI_TWITTER_ACCESS_SECRET,
        )

        openai = OpenAI()

        # Categorized prompts
        general_prompts = [
            "You're a clever and engaging Twitter influencer. Respond to this tweet in a way that sparks conversation, using humor and insights:",
            "You're a sharp conversationalist. Reply to this tweet with a relatable and thought-provoking comment to drive discussion:",
            "You have a great sense of humor and insight. Craft a witty response to this tweet that will make people reflect and engage:",
        ]

        controversial_prompts = [
            "As a provocative thinker, reply to this tweet with a controversial opinion that sparks engagement, while keeping it within respectful guidelines:",
            "You’re an outspoken Twitter user. Respond to this tweet with a thought-provoking comment about a divisive topic that will drive discussion:",
        ]

        humorous_prompts = [
            "You’re known for your humor. Reply to this tweet with a playful comment that will make people laugh and share it:",
            "Respond with a pun or a funny quip that will get your followers laughing and retweeting:",
        ]

        motivational_prompts = [
            "You're an inspirational figure. Respond to this tweet with a positive message that lifts people up and motivates them:",
            "Share a motivational and uplifting comment in response to this tweet that will leave others feeling inspired:",
        ]

        specialized_sports_prompts = [
            "You're a sports fanatic. Respond to this tweet with a witty sports-related analogy or joke that engages fans of the game:"
        ]

        specialized_tech_prompts = [
            "You're a tech enthusiast. Craft a reply to this tweet that highlights an interesting or clever insight about the latest in technology trends:"
        ]

        specialized_music_prompts = [
            "You love music and can easily weave it into conversations. Respond to this tweet with a music-related joke or reference:"
        ]

        specialized_movies_tv_prompts = [
            "You're a big fan of film and TV. Craft a response to this tweet that references a popular show or movie in a witty way:"
        ]

        specialized_food_prompts = [
            "You're a foodie at heart. Respond to this tweet with a clever comment or funny quip related to food or cooking:"
        ]

        specialized_travel_prompts = [
            "You're an avid traveler. Share an engaging comment or thought about travel experiences that will spark curiosity in response to this tweet:"
        ]

        specialized_pets_prompts = [
            "You're an animal lover. Respond to this tweet with a cute or funny pet-related comment that your followers will adore:"
        ]

        specialized_fashion_prompts = [
            "You have a keen eye for style. Respond to this tweet with a fashion-forward comment that will resonate with trendy followers:"
        ]

        specialized_fitness_prompts = [
            "You're a fitness enthusiast. Reply to this tweet with a motivational or insightful comment about health and wellness:"
        ]

        specialized_diy_prompts = [
            "You’re a creative DIYer. Share a clever home decor tip or a funny DIY experience in response to this tweet:"
        ]

        specialized_gaming_prompts = [
            "You're a gamer and love discussing the latest games. Respond to this tweet with a fun gaming reference or insider joke that resonates with fellow gamers:"
        ]

        specialized_politics_prompts = [
            "As someone interested in politics, respond to this tweet with a thoughtful comment or opinion on current political issues in a respectful manner:"
        ]

        specialized_education_prompts = [
            "You're an education advocate. Reply to this tweet with a thought-provoking or insightful comment about learning, education, or personal growth:"
        ]

        specialized_environment_prompts = [
            "As an environmental advocate, respond to this tweet with a comment that highlights an important eco-friendly issue or solution:"
        ]

        specialized_entrepreneurship_prompts = [
            "You're an entrepreneur with an eye for opportunity. Respond to this tweet with an insightful comment about startups, business strategies, or innovation:"
        ]

        sarcastic_prompts = [
            "You're a master of sarcasm. Reply to this tweet with a witty and playful comeback that will entertain followers while keeping the tone light:"
        ]

        # Combine all prompts into one dictionary for easier use
        categorized_prompts = {
            "general": general_prompts,
            "controversial": controversial_prompts,
            "humorous": humorous_prompts,
            "motivational": motivational_prompts,
            "specialized_sports": specialized_sports_prompts,
            "specialized_tech": specialized_tech_prompts,
            "specialized_music": specialized_music_prompts,
            "specialized_movies_tv": specialized_movies_tv_prompts,
            "specialized_food": specialized_food_prompts,
            "specialized_travel": specialized_travel_prompts,
            "specialized_pets": specialized_pets_prompts,
            "specialized_fashion": specialized_fashion_prompts,
            "specialized_fitness": specialized_fitness_prompts,
            "specialized_diy": specialized_diy_prompts,
            "specialized_gaming": specialized_gaming_prompts,
            "specialized_politics": specialized_politics_prompts,
            "specialized_education": specialized_education_prompts,
            "specialized_environment": specialized_environment_prompts,
            "specialized_entrepreneurship": specialized_entrepreneurship_prompts,
            "sarcastic": sarcastic_prompts,
        }

        def categorize_tweet(tweet_text, model="gpt-4o-mini"):
            print("categorizing tweet")
            categorization_prompt = (
                "Categorize the following tweet into one of these categories: "
                "general, controversial, humorous, motivational, specialized_sports, specialized_tech, "
                "specialized_music, specialized_movies_tv, specialized_food, specialized_travel, specialized_pets, "
                "specialized_fashion, specialized_fitness, specialized_diy, specialized_gaming, specialized_politics, "
                "specialized_education, specialized_environment, specialized_entrepreneurship, sarcastic. "
                "The categories are defined as:\n"
                "1. General: Clever, engaging, thought-provoking, or insightful responses.\n"
                "2. Controversial: Thought-provoking, opinion-driven, engaging but within guidelines.\n"
                "3. Humorous: Funny, light-hearted, pun-filled, pop culture references.\n"
                "4. Motivational: Uplifting, positive messages.\n"
                "5. Specialized: Sports, tech, music, movies, food, travel, pets, fashion, fitness, DIY, gaming, politics, education, environment, entrepreneurship.\n"
                "6. Sarcastic: Witty, playful comebacks with a humorous, sometimes ironic tone.\n"
                'Tweet: "' + tweet_text + '"\n\nCategory:'
            )

            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a popular Twitter influencer that is skilled in tweeting viral content.",
                    },
                    {"role": "user", "content": categorization_prompt},
                ],
            )
            category = response.choices[0].message.content.strip().lower()
            return category

        def get_google_trends():
            print("getting google trends")
            pytrends = TrendReq()

            use_realtime = False
            if use_realtime:
                trending_searches = pytrends.realtime_trending_searches(pn="US")
                trends = trending_searches["title"].tolist()
            else:
                trending_searches = pytrends.trending_searches()
                trends = trending_searches[0].tolist()

            return trends

        def get_combined_trends(api, woeid=1):
            print("getting trends")
            # twitter_trends = get_twitter_trends(api, woeid)
            twitter_trends = []
            google_trends = get_google_trends()
            print(google_trends)
            combined_trends = list(set(twitter_trends + google_trends))
            return combined_trends

        def get_trend_context(trend, dopeshi_client):
            print(f"getting trend context: {trend}")
            # return get_from_ai(trend)
            response = get_trend_from_tweets(trend, dopeshi_client)
            print(response)
            return response

        def get_trend_from_tweets(trend, dopeshi_client):
            trend = trend.replace(":", "-")
            tweets = dopeshi_client.search_recent_tweets(query=trend, max_results=10)
            tweets_text = " ||| ".join([tweet.text for tweet in tweets.data])

            prompt = (
                f"Summarize why the following topic is trending based on the provided tweets separated by |||:\n\n"
                f"Topic: {trend}\n\n"
                f"Tweets: {tweets_text}\n\n"
                f"Summary:"
            )

            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are skilled in summarizing topics based on multiple tweets separated by |||, your job is to summarize the tweets in a way that it can later be categorized into a general, controversial, humorous, motivational, or specialized category. Your response should be in json format with the following keys: category, trend, summary.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            summary = completion.choices[0].message.content
            return summary

        def generate_own_tweet(trend, context, model="gpt-4o-mini"):
            print("generating own tweet")
            category = categorize_tweet(context)
            prompt = {
                "general": random.choice(general_prompts),
                "controversial": random.choice(controversial_prompts),
                "humorous": random.choice(humorous_prompts),
                "motivational": random.choice(motivational_prompts),
                "specialized_sports": random.choice(specialized_sports_prompts),
                "specialized_tech": random.choice(specialized_tech_prompts),
                "specialized_music": random.choice(specialized_music_prompts),
                "specialized_movies_tv": random.choice(specialized_movies_tv_prompts),
                "specialized_food": random.choice(specialized_food_prompts),
                "specialized_travel": random.choice(specialized_travel_prompts),
                "specialized_pets": random.choice(specialized_pets_prompts),
                "specialized_fashion": random.choice(specialized_fashion_prompts),
                "specialized_fitness": random.choice(specialized_fitness_prompts),
                "specialized_diy": random.choice(specialized_diy_prompts),
                "specialized_gaming": random.choice(specialized_gaming_prompts),
                "specialized_politics": random.choice(specialized_politics_prompts),
                "specialized_education": random.choice(specialized_education_prompts),
                "specialized_environment": random.choice(
                    specialized_environment_prompts
                ),
                "specialized_entrepreneurship": random.choice(
                    specialized_entrepreneurship_prompts
                ),
                "sarcastic": random.choice(sarcastic_prompts),
            }.get(category, random.choice(general_prompts))

            prompt += f"""You are a popular Twitter influencer known for your {category} tweets. Craft a tweet about '{trend}' based on the following context. 
                 Make sure to keep it under 250 characters, use casual language, and sound like a Gen Z influencer. 
                 Don't include unnecessary hashtags, Do NOT include any emojis.
                 Context: "{context}"
                 Tweet:"""

            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Gen Z influencer known for your viral tweets. Do not include emojis in your response.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            tweet = response.choices[0].message.content.strip('"')
            return tweet

        def post_own_tweet(dopeshi_client):
            print("posting own tweet")
            trends = get_combined_trends(dopeshi_client)
            if trends:
                trend = random.choice(trends)
                context = get_trend_context(trend, dopeshi_client)
                tweet = generate_own_tweet(trend, context)
                print(context, tweet)

                try:
                    response = dopeshi_client.create_tweet(text=tweet)
                    print(f"Posted tweet: {tweet}")
                    # print(response.data['id'])
                except tweepy.errors.Forbidden as e:
                    print(f"Error: {e}")

        # def schedule_posts(api):
        #     peak_hours = [9, 12, 15, 18, 21]  # Example peak hours
        #     off_peak_hours = [0, 3, 6]  # Example off-peak hours

        #     for hour in peak_hours:
        #         schedule.every().day.at(f"{hour}:00").do(post_own_tweet, api=api)
        #         schedule.every().day.at(f"{hour}:30").do(post_own_tweet, api=api)

        #     for hour in off_peak_hours:
        #         schedule.every().day.at(f"{hour}:00").do(post_own_tweet, api=api)

        #     while True:
        #         schedule.run_pending()
        #         time.sleep(1)

        # # Schedule own posts
        # schedule_posts(api)

        # my own changes here
        post_own_tweet(dopeshi_client)
