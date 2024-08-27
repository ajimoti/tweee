from pytrends.request import TrendReq
import openai
import tweepy


def get_trending_topics():
    pytrends = TrendReq(hl="en-US", tz=360)
    trending_searches_df = pytrends.trending_searches(
        pn="united_states"
    )  # or any other region
    return trending_searches_df[0].tolist()


def get_google_trends(use_realtime=False):
    pytrends = TrendReq(hl="en-US", tz=360)

    if use_realtime:
        trending_searches = pytrends.realtime_trending_searches(pn="united_states")
        trends = trending_searches["title"].tolist()
    else:
        trending_searches = pytrends.trending_searches()
        trends = trending_searches[0].tolist()

    return trends


def generate_summary(topic):
    response = openai.Completion.create(
        model="text-davinci-003", prompt=f"Why is '{topic}' trending?", max_tokens=60
    )
    summary = response.choices[0].text.strip()
    return summary


def tweet_summary(summary):
    auth = tweepy.OAuthHandler("consumer_key", "consumer_secret")
    auth.set_access_token("access_token", "access_token_secret")
    api = tweepy.API(auth)
    api.update_status(summary)
