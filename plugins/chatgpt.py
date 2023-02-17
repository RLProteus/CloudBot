from cloudbot import hook
from cloudbot.bot import bot
import requests
import textwrap


@hook.command("gpt", autohelp=False)
def chat_gpt(nick, chan, text):
    prompt = (
        f"{nick} on IRC channel {chan} says: {text}\n"
    )
    open_ai_api_key = bot.config.get_api_key("openai")
    resp = requests.post("https://api.openai.com/v1/completions",
                           headers={
                             "Authorization": f"Bearer {open_ai_api_key}",
                           },
                           json={
                               "model": "text-davinci-003",
                               "prompt": prompt,
                               "max_tokens": 1024,
                               "temperature": 1,
                               "n": 1,
                               "stream": False,
                               "user": f"{hash(nick)}",
                           }
    )
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["text"].replace("\n","")
        messages = textwrap.wrap(answer,250)
        if len(messages) > 2:
            # Send the prompt to hastebin
            hastebin_api_key = bot.config.get_api_key("hastebin")
            hastebin_resp = requests.post("https://hastebin.com/documents",
                                          headers={
                                              "Authorization": f"Bearer {hastebin_api_key}",
                                              "Content-Type": "text/plain"
                                          },
                                          data="\n".join(messages)
            )
            if hastebin_resp.status_code == 200:
                # Return first 2 blocks, then direct to hastebin
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
