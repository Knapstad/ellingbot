import tweepy
import config
import math

auth = tweepy.OAuthHandler(config.API_key, config.API_secret_key)
auth.set_access_token(config.access_token, config.access_token_secret)

api = tweepy.API(auth)


def load_tekst():
    with open("elling.json") as file:
        tekst = json.load(file)
    return tekst


def post_tweet(message):
    api.update_status(message)


def devide_post(message):
    if len(message) > 240:
        parts = math.ceil(len(message) / 240)
        message = message.split(".")

        messagelength = math.ceil(len(message) / parts)
        chunks = [
            message[i : i + messagelength]
            for i in range(0, len(message), messagelength)
        ]
        message_chunks = []
        for i, j in enumerate(chunks):
            message_chunks.append(" ".join(j).strip() + f" {i+1}/{len(chunks)}")
        return message_chunks
    else:
        return [message]
