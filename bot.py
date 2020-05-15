import tweepy
import config

auth = tweepy.OAuthHandler(config.API_key, config.API_secret_key)
auth.set_access_token(config.access_token, config.access_token_secret)
