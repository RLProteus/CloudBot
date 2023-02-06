from cloudbot import hook
from cloudbot.bot import bot
import requests


@hook.command("gpt", autohelp=False)
def chat_gpt(nick, chan, text):
    prompt = (
        f"Answer the following message from user {nick} on IRC channel {chan}.\n"
        f"{text}\n"
    )
    api_key = bot.config.get_api_key("openai")
    resp = requests.post("https://api.openai.com/v1/completions",
                           headers={
                             "Authorization": f"Bearer {api_key}",
                           },
                           json={
                               "model": "text-davinci-003",
                               "prompt": prompt,
                               "max_tokens": 100,
                               "temperature": 1,
                               "n": 1,
                               "stream": False,
                               "user": f"{hash(nick)}",
                           }
    )
    if resp.status_code == 200:
        return resp.json()["choices"][0]["text"].replace("\n","")
    else:
         return f"ChatGPT failed with error code {resp.status_code} and message {resp.json()}"
