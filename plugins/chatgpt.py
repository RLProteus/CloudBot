from datetime import datetime, timedelta
import textwrap
import re
import shutil
import os
import random
import string
import requests

from cloudbot import hook
from cloudbot.bot import bot



RATELIMIT = {}
CONTEXT = {
    "messages": [
        {
        "role": "system",
        "content": "",
        "name": "system",
        "timestamp": datetime.now().strftime('%m/%d/%y %H:%M:%S')
        }
    ]
}

def check_rate_limit(nick, event):
    permission_manager = event.conn.permissions
    user = event.mask
    user_permissions = permission_manager.get_user_permissions(user.lower())

    if "op" in user_permissions or "botcontrol" in user_permissions:
        return True
    if RATELIMIT.get(nick, False) == False:
        return True
    time_difference = abs(datetime.now() - RATELIMIT.get(nick))
    if time_difference.seconds > 300:
        return True
    time_left =  (RATELIMIT.get(nick) + timedelta(minutes=5)) - datetime.now()
    return f"You are rate limited ! Try again in {time_left.seconds} seconds !"

def add_to_rate_limit(nick):
    RATELIMIT[nick] = datetime.now()


def build_context(nick, text, role):
    if CONTEXT.get("idle_timestamp"):
        idle_timestamp = datetime.strptime(CONTEXT.get("idle_timestamp"),'%m/%d/%y %H:%M:%S')
        if abs(datetime.now() - idle_timestamp).seconds > 300:
            drop_context()

    CONTEXT.get("messages").append({
        "role": role,
        "content": f"{text}",
        "name": nick,
        "timestamp": datetime.now().strftime('%m/%d/%y %H:%M:%S')
        })

    CONTEXT.update({"idle_timestamp": datetime.now().strftime('%m/%d/%y %H:%M:%S')})

def drop_context():
    messages = CONTEXT.get("messages").copy()
    for message in messages:
        if message["role"] != "system":
            CONTEXT.get("messages").remove(message)

@hook.command("gpt_get_system")
def get_system_message():
    system = CONTEXT.get("messages")[0].get("content")
    return f"Current system message: {system}"

@hook.command("gpt_set_system")
def set_system_message(nick, chan, text, event):
    CONTEXT.get("messages")[0].update({"content":text})
    CONTEXT.get("messages")[0].update({"timestamp": datetime.now().strftime('%m/%d/%y %H:%M:%S')})
    return f"System prompt has been updated to {text}"

@hook.command("gpt_drop_context")
def drop_context_hook():
    drop_context()
    return "Context has been dropped !"

@hook.command("gpt_get_context", permissions=["botcontrol", "op"])
def get_context():
    return CONTEXT.get("messages")

@hook.command("gpt", autohelp=False)
def chat_gpt(nick, text):
    build_context(nick, text, role="user")
    open_ai_api_key = bot.config.get_api_key("openai")
    resp = requests.post("https://api.openai.com/v1/chat/completions",
                           headers={
                             "Authorization": f"Bearer {open_ai_api_key}",
                           },
                           json={
                               "model": "gpt-4o",
                               "messages": CONTEXT.get("messages"),
                               "max_tokens": 1024,
                               "temperature": 1,
                               "n": 1,
                               "stream": False,
                               "user": f"{hash(nick)}",
                           }
    , timeout=30)
    add_to_rate_limit(nick)
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"].replace("\n","")
        build_context(nick="Karmachameleon", text=answer, role="assistant")
        messages = textwrap.wrap(answer,420)
        if len(messages) > 3:
            hastebin_api_key = bot.config.get_api_key("hastebin")
            hastebin_resp = requests.post("https://hastebin.com/documents",
                                          headers={
                                              "Authorization": f"Bearer {hastebin_api_key}",
                                              "Content-Type": "text/plain"
                                          },
                                          data="\n".join(messages)
            , timeout=30)
            if hastebin_resp.status_code == 200:
                truncated_resp = messages[0:3]
                truncated_resp.append(f"Find the rest of the answer here: https://hastebin.com/share/{hastebin_resp.json()['key']}")
                return truncated_resp

            return "Hastebin failed with error {hastebin_resp.status_code} and message: {hastebin_resp.json()}"
        return messages
    return textwrap.wrap(
        f"ChatGPT failed with error code {resp.status_code}",
        250
    )

@hook.command("gpt_image", autohelp=False)
def chat_gpt_image(nick, chan, text, event):
    open_ai_api_key = bot.config.get_api_key("openai")
    resp = requests.post("https://api.openai.com/v1/images/generations",
                           headers={
                             "Authorization": f"Bearer {open_ai_api_key}",
                             "Content-Type": "application/json"
                           },
                           json={
                               "model": "dall-e-3",
                               "prompt": text,
                               "n": 1,
                               #"quality": "hd",
                               #"size":"1024x1792"


                           }
    , timeout=30)
    add_to_rate_limit(nick)
    if resp.status_code == 200:
        answer = resp.json()["data"][0]["url"]
        img = requests.get(answer, stream = True, timeout=30)
        with open("temp.png",'wb') as f:
            shutil.copyfileobj(img.raw, f)
        upload_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        os.system(f'curl -X POST --data-binary @temp.png     -H "Authorization: Bearer $(gcloud auth print-access-token)"     -H "Content-Type: image/png"     "https://storage.googleapis.com/upload/storage/v1/b/gavibot-ai-images/o?uploadType=media&name={upload_name}.png"')

        return f"https://storage.googleapis.com/gavibot-ai-images/{upload_name}.png"
    return textwrap.wrap(
        f"ChatGPT failed with error code {resp.status_code}",
        250
    )

message = re.compile('^karmachameleon.*',re.IGNORECASE)


#@hook.regex(message)
#def chat_gpt_re(nick, chan, content, event):
#    text = content.lower().split('karmachameleon')[1]
#    return chat_gpt(nick, chan, text, event)
