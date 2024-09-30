import requests
import json
import datetime


from cloudbot import hook
from cloudbot.event import EventType

markov_model = {}


@hook.command("declare", autohelp=True)
def declare(text, message):
    """[nick] - Outputs Marvok chain based on input's past logs"""
    #markov_users = ("echs", "knots", "ngwnn", "nullaffinity", "skeer", "gavisann", "spr1ng", "mobomelter", "umbra", "wabb1t", "esses", "xoted","computerkiller","silentfury","jamesgamble","sre", "grabs","slaughter", "witsh", "trump", "shad")
    #
    #if text.lower() in markov_users:
    r = requests.get("https://markovify-api.gavibot.com/response?user={0}".format(text.lower()))
    if r.status_code == 200:
        out = r.content
        out = out.decode()

        message("{0} says: {1}".format(text, out))
    elif r.status_code == 404:
        out = r.content
        out = out.decode()
        message(out)
    else:
        message(f"Error: Status code: {r.status_code}")
    #print(out)
    #else:
    #    message("User has not been added yet. THIS SHIT IS A BETA YO")


@hook.event([EventType.message,], singlethread=True)
def forward_events(event, message):
    url = f'https://markovify-api.gavibot.com/ingest?user={event.nick.lower()}'
    #event_json = {f'user': '{event.nick}',"message": "{event.content}"}
    event_json ={'timestamp':f'{datetime.datetime.now().isoformat()}','message': f'{event.content}'}
    try:
        requests.post(url, json = event_json)
    except Exception as e:
        print(e)



@hook.command("declare_build", autohelp=True, permissions=["op"])
def declare_build(text, message):
    """[nick] - Builds Marvok chain model based on input's past logs"""
    try:
        r = requests.get("https://markovify-api.gavibot.com/build-model?user={0}".format(text.lower()))
        if r.status_code == 201:
            message("Build completed")
        else:
            message(f"Error: Status code: {r.status_code}")
    except Exception as e:
        message("Unknown error occurred")

@hook.command("declare_status", autohelp=True)
def declare_status(text, message):
    """[nick] - Provides information about the status of this user's declares"""
   
    r = requests.get("https://markovify-api.gavibot.com/status?user={0}".format(text.lower()))
    try:
        if r.status_code == 200:
            user_object = json.loads(r.content)
            #message(user_object)
            status, enabled, backlog = [""]*3

            status= user_object[text.lower()]['status']
            enabled = user_object[text.lower()]['enabled']
            if user_object[text.lower()]['notes'] == 'notuptodate':
                backlog = "Missing some backlog"
            elif user_object[text.lower()]['notes'] == 'uptodate':
                backlog = "Backlog complete and ingest enabled"

            message(f"\x02User\x02: {text.lower()}, \x02Enabled\x02: {enabled}, \x02Status\x02: {status}, \x02Backlog\x02: {backlog}")

        else:
            message(f"Error: Status code: {r.content.decode()}")
    except Exception as e:
        message("Unknown error occurred")


    