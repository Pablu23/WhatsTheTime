import time
from datetime import datetime, timezone

import keyboard
import requests
import tweepy

# Keys is a simple py file with just a Dictionary in it.
from keys import keys
'''
The structure of the dictionary is like this:

keys = dict(
    access_token='XXXXXXXXXXXXXXXXXXXX',
    access_secret='XXXXXXXXXXXXXXXXXXXX',
    bearer_token="XXXXXXXXXXXXXXXXXXXX",
    consumer_key='XXXXXXXXXXXXXXXXXXXX',
    consumer_secret='XXXXXXXXXXXXXXXXXXXX'
)
'''

# Read keys, tokens and secrets from secret file to not expose the keys in code
bearer_token = keys["bearer_token"]
consumer_key = keys["consumer_key"]
consumer_secret = keys["consumer_secret"]
acces_token = keys["access_token"]
acces_secret = keys["access_secret"]

# Setup tweepy Library to communicate to the twitter Api easier
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(acces_token, acces_secret)
api = tweepy.API(auth)


def bearer_oauth(r):
    # Used for authentication for the Twitter v2 api
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2UserMentionsPython"
    return r


def connect_to_endpoint(url, params):
    # Send a GET request to the api and receive a json reponse
    response = requests.request("GET", url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )

    # Return the json string response as json Object
    return response.json()


def get_usernames(ids):
    usernames = []

    # Api Interface address to get usernames from ids
    url = "https://api.twitter.com/2/users"
    ids_as_string = ','.join(ids)
    params = {"ids": ids_as_string}

    # Send a GET request to the api and receive a json reponse
    response = requests.request("GET", url, auth=bearer_oauth, params=params)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )

    # Convert the string response to json Object
    response = response.json()

    # Get the json response "Data" field and from there get the Usernames and append them to a list
    for data in response["data"]:
        username = data["username"]
        usernames.append(f"@{username}")
    return usernames


def send_response(users):
    users_as_string = ' '.join(users)
    now = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
    tweet = f"{users_as_string} the time right now is {now} CET"
    print(f"[INFO] Tweet: \"{tweet}\" got send")

    # Through the Tweepy library I send the Tweet
    api.update_status(tweet)


def main():
    while(True):
        # Url for a later Methode to get all tweets with a Mention at me (This is the api interface address for Mentions)
        # The number "722101487409750016" is my Id, with this I only get Mentions at me
        url = "https://api.twitter.com/2/users/722101487409750016/mentions"

        # Get the Current time in UTC because the twitter API works with UTC
        timeStr = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"[INFO] Datetime is now: {timeStr}")

        # Waiting 90 Seconds to not go above my Twitter Api status Rate limit
        print("[INFO] Now waiting 90 seconds")
        for i in range(90):
            # Its shit but if the q key is pressed the programm closes
            # Problem with this is you have to hold q to hit it when the programm is not frozen
            if keyboard.is_pressed('q'):
                print("[INFO] Done.")
                exit()
            time.sleep(1)

            # end="\r" is so the next print in the loop will overwrite the last Message and not cludder up the terminal too badly
            print(f"[INFO] {i} / 90", end="\r")
        print(f"[INFO] {i} / 90")

        # Parameter found here https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-mentions
        # These parameters dictate what informations and what kind of tweets I get as a reply
        params = {"tweet.fields": "created_at,text,author_id",
                  "start_time": timeStr}

        print("[INFO] Sending mention request")
        json_response = connect_to_endpoint(url, params)
        print("[INFO] Request was successful")
        responses_to = []

        # From the json response I get the "Meta" type to see how many tweet responses I got
        meta = json_response["meta"]
        result_count = meta["result_count"]
        print(f"[INFO] {result_count} : Results were found")
        if result_count >= 1:

            # From the json response I get the "data" Type to go through
            for data in json_response["data"]:

                # From the "data" type I get the "text" Type
                if data["text"] is not None:

                    # If the "text" Type is not None and contains the string "whats the time"
                    # I will add the "author_id" from data to a list
                    if "whats the time" in data["text"].lower():
                        responses_to.append(data["author_id"])
            length_responses = len(responses_to)
            if length_responses >= 1:
                print(f"[INFO] Responding to {length_responses} requests")

                # From the list of author_ids I get the specific usernames to @ in my tweet
                usernames = get_usernames(responses_to)
                print(f"[INFO] Responding to {usernames}")

                # The response is send to the Users that requested it
                send_response(usernames)
            else:
                print("[INFO] No requests")
        responses_to = None


if __name__ == "__main__":
    main()
