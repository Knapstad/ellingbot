import json
import math
from functools import wraps
from typing import Any, Tuple

import tweepy

import config
from google.cloud import storage
from google.oauth2 import service_account


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
    data: Any,
    blob_name: str,
    bucket_name: str,
):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    if not blob:
        blob = bucket.blob(blob_name)
    blob.upload_from_string(str(data))


def load_tekst(client):
    tekst = load_from_cloud(client, config.text_blob_name, config.bucket_name)
    return json.loads(tekst)


def load_index(client):
    index = load_from_cloud(client, config.index_blob_name, config.bucket_name)
    return json.loads(index)


def save_index(index, client):
    save_to_cloud(client, index, config.index_blob_name, config.bucket_name)


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


def main(*args, **kwargs):

    SCOPES = ["https://www.googleapis.com/auth/devstorage.read_write"]
    CREDENTIALS = service_account.Credentials.from_service_account_file(
        config.cloud_credentials, scopes=SCOPES
    )

    INDEX_BLOB_NAME = config.index_blob_name
    TEXT_BLOB_NAME = config.text_blob_name
    BUCKET_NAME = config.bucket_name

    client = storage.Client(project=config.bucket_name, credentials=CREDENTIALS)

    tekst = load_tekst(client)
    index = load_index(client)

    try:
        message = tekst[index]
        while message.isupper():
            index += 1
            message += tekst[index]
        for i in devide_post(message):
            post_tweet(i)
        index += 1
        save_index(index, client)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    pass
