import json
import math
from functools import wraps
from typing import Any, Tuple

import tweepy

import config
from google.cloud import storage
from google.oauth2 import service_account
from myerrors import NotAuthenticated, NotFound

auth = tweepy.OAuthHandler(config.API_key, config.API_secret_key)
auth.set_access_token(config.access_token, config.access_token_secret)

api = tweepy.API(auth)


def retry_on_connection_error(max_retry: int = 3):
    def decorate_function(function):
        @wraps(function)
        def retry(*args, **kwargs):
            tries = 0
            while tries < max_retry:
                try:
                    return function(*args, **kwargs)
                except ConnectionError:
                    tries += 1
            return function(*args, **kwargs)

        return retry

    return decorate_function


@retry_on_connection_error()
def load_from_cloud(
    client: "google.cloud.storage.client.Client", blob_name: str, bucket_name: str
):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string()


@retry_on_connection_error()
def save_to_cloud(
    client: "google.cloud.storage.client.Client",
    data: list,
    blob_name: str,
    bucket_name: str,
):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    if not blob:
        blob = bucket.blob(blob_name)
    blob.upload_from_string(str(data))


def load_tekst():
    with open("elling.json") as file:
        tekst = json.load(file)
    return tekst


def load_index():
    with open("index.json") as file:
        return json.load(file)


def save_index(index):
    with open("index.json", "w") as file:
        json.dump(index, file)


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


def main():
    tekst = load_tekst()
    index = load_index()

    try:
        message = tekst[index]
        while message.isupper():
            index += 1
            message += tekst[index]
        for i in devide_post(message):
            post_tweet(i)
        index += 1
        save_index(index)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
