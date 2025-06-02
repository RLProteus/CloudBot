import random
import string
import json
import textwrap
from base64 import b64decode

from agents import (
    Agent,
    Runner,
    WebSearchTool,
    ImageGenerationTool,
    FunctionTool,
    function_tool,
    set_default_openai_key,
    TResponseInputItem
)

from google.cloud import storage

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import web

set_default_openai_key(bot.config.get_api_key("openai"))

CONTEXT: list[TResponseInputItem] = []

@function_tool()
@hook.command("dump_context", autohelp=False)
async def dump_context():
    """
    dump_context deletes the current context and history of the conversation.
    """
    global CONTEXT
    CONTEXT = []

    return "The context has been cleared."


web_agent = Agent(
    name="Web Assistant",
    instructions="Be a helpful assistant. You can search the web for information.",
    handoff_description="Use this agent for searching the web for information.",
    tools=[
        WebSearchTool(),
    ]
)

default_agent = Agent(
    name="Gloria",
    instructions="Be a helpful assistant.",
    tools=[
        web_agent.as_tool(
             tool_name="web_search",
             tool_description="Search the web for information and provide relevant results."
        ),
        ImageGenerationTool(tool_config={
            "type": "image_generation",
            "model": "gpt-image-1",
            "size": "1024x1024"
        }),
        dump_context
    ]
)

@hook.command("gloria","gpt","gpt_image", autohelp=False)
async def gpt_multi_agent(nick, text):
    """
    gpt_multi_agent allows users to interact with multiple agents based on the context of the request.

    args:
        nick: The nickname of the user making the request.
        text: The text of the request.
    returns:
        A list of messages containing the response from the agents.
    """

    CONTEXT.append({"content": f"{nick} says: {text}", "role": "user", "type": "message"})
    result = await Runner.run(default_agent, CONTEXT)

    with open("context.json",'w') as f:
        f.write(json.dumps(CONTEXT, indent=2))
    output = f"[{result.last_agent.name}]: {result.final_output}"
    for item in result.new_items:
        if (
            item.type == "tool_call_item"
            and item.raw_item.type == "image_generation_call"
            and (img_result := item.raw_item.result)
        ):
            with open("temp.png",'wb') as f:
                f.write(b64decode(img_result))
            upload_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7)) + '.png'
            storage_client = storage.Client()
            bucket = storage_client.bucket("gavibot-ai-images")
            blob = bucket.blob(upload_name)
            blob.upload_from_filename("temp.png")
            output += f" Image link: https://storage.googleapis.com/gavibot-ai-images/{upload_name}"
            CONTEXT.append({"id": item.raw_item.id})
        else:
            CONTEXT.append(item.to_input_item())
    messages = textwrap.wrap(output,420)
    if len(messages) > 3:
        truncated_resp = messages[0:3]
        truncated_resp.append(f"Find the rest of the answer here: {web.paste(output,ext='md',service='mozilla')}")
        return truncated_resp
    return messages

