from cloudbot import hook
from cloudbot.bot import bot
from datetime import datetime, timedelta
import requests
import textwrap


RATELIMIT = {}
SYSTEM = ""

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
    pass

@hook.command("gpt_get_system")
def get_system_message():
    return f"Current system message: {SYSTEM}"

@hook.command("gpt_set_system")
def set_system_message(nick, chan, text, event):
    global SYSTEM
    SYSTEM = text
    return f"System prompt has been updated to {SYSTEM}"


@hook.command("gpt", autohelp=False)
def chat_gpt(nick, chan, text, event):
    rate_limit = check_rate_limit(nick, event)
    prompt = "\n".join([
        SYSTEM,
        f"{nick} on IRC channel {chan} says: {text}"
    ])
    open_ai_api_key = bot.config.get_api_key("openai")
    resp = requests.post("https://api.openai.com/v1/chat/completions",
                           headers={
                             "Authorization": f"Bearer {open_ai_api_key}",
                           },
                           json={
                               "model": "gpt-3.5-turbo",
                               "messages": [{
                                   "role": "user",
                                   "content": prompt,
                                   "name": nick}],
                               "max_tokens": 1024,
                               "temperature": 1,
                               "n": 1,
                               "stream": False,
                               "user": f"{hash(nick)}",
                           }
    )
    add_to_rate_limit(nick)
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"].replace("\n","")
        messages = textwrap.wrap(answer,250)
        if len(messages) > 2:
            hastebin_api_key = bot.config.get_api_key("hastebin")
            hastebin_resp = requests.post("https://hastebin.com/documents",
                                          headers={
                                              "Authorization": f"Bearer {hastebin_api_key}",
                                              "Content-Type": "text/plain"
                                          },
                                          data="\n".join(messages)
            )
            if hastebin_resp.status_code == 200:
                truncated_resp = messages[0:2]
                truncated_resp.append(f"Find the rest of the answer here: https://hastebin.com/share/{hastebin_resp.json()['key']}") 
                return truncated_resp
            else:
                return "Hastebin failed with error {hastebin_resp.status_code} and message: {hastebin_resp.json()}"
        return messages
    else:
         return textwrap.wrap(
             f"ChatGPT failed with error code {resp.status_code} and message: {resp.json()['error']['message']}",
             250
         )
