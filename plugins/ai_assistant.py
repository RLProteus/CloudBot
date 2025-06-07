import random
import string
import json
import textwrap
from base64 import b64decode
from datetime import datetime, timedelta

from agents import (
    Agent,
    Runner,
    RunResult,
    WebSearchTool,
    ImageGenerationTool,
    CodeInterpreterTool,
    function_tool,
    set_default_openai_key,
    TResponseInputItem
)

from google.cloud import storage

from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import web

set_default_openai_key(bot.config.get_api_key("openai"))

CONTEXT_TIMESTAMP = ""
CONTEXT: list[TResponseInputItem] = []
CONTEXT_DEBUG = False

@function_tool()
@hook.command("drop_context", autohelp=False)
async def drop_context():
    """
    drop_context deletes the current context and history of the conversation.
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
code_agent = Agent(
    name="Code Assistant",
    instructions="Be a helpful assistant. You can write code and answer programming questions.",
    handoff_description="Use this agent for writing code and answering programming questions.",
    tools=[
        CodeInterpreterTool(
                tool_config={"type": "code_interpreter", "container": {"type": "auto"}},
            )
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
        code_agent.as_tool(
            tool_name="code_interpreter",
            tool_description="use to run code interpreter tasks such as running code and answering math questions."
        ),
        drop_context
    ]
)

def image_upload(image_data: str) -> str:
    """
    Uploads an image to a Google Cloud Storage bucket and returns the public URL.

    args:
        image_data: The base64 encoded image data.
    returns:
        The public URL of the uploaded image.
    """
    with open("temp.png",'wb') as f:
        f.write(b64decode(image_data))
    upload_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7)) + '.png'
    storage_client = storage.Client()
    bucket = storage_client.bucket("gavibot-ai-images")
    blob = bucket.blob(upload_name)
    blob.upload_from_filename("temp.png")
    return f"https://storage.googleapis.com/gavibot-ai-images/{upload_name}"

def parse_response(result: RunResult) -> str:
    """
    Parses the response from the agent and formats it for output.

    args:
        result: The raw response from the agent.
    returns:
        A formatted string containing the response.
    """
    output = f"[{result.last_agent.name}]: {result.final_output}"

    for item in result.new_items:
        if (
            item.type == "tool_call_item"
            and item.raw_item.type == "image_generation_call"
            and (img_result := item.raw_item.result)
        ):
            gcp_filename = image_upload(img_result)
            output += f" Image link: https://storage.googleapis.com/gavibot-ai-images/{gcp_filename}"
            CONTEXT.append({"id": item.raw_item.id})
        else:
            CONTEXT.append(item.to_input_item())
    messages = textwrap.wrap(output,420)
    if len(messages) > 3:
        truncated_resp = messages[0:3]
        truncated_resp.append(f"Find the rest of the answer here: {web.paste(output,ext='md',service='dpaste')}")
        return truncated_resp
    return messages

@hook.command("gloria_debug", autohelp=False)
def debug_context():
    """
    Toggles logging for the current context.
    """
    global CONTEXT_DEBUG
    if CONTEXT_DEBUG:
        CONTEXT_DEBUG = False
        return "Debugging disabled. Context will not be logged."
    else:
        CONTEXT_DEBUG = True
        return("Debugging enabled. Context will be logged.")

def check_idle_context(thresh: int) -> bool:
    """
    This method returns true if the context has been idle for more than threshold in seconds. 
    """
    global CONTEXT_TIMESTAMP
    if CONTEXT_TIMESTAMP is not "":
       idle_timestamp = datetime.strptime(CONTEXT_TIMESTAMP, '%m/%d/%y %H:%M:%S')
       if abs(datetime.now() - idle_timestamp).seconds > thresh:
           return True
    return False

def build_context(nick: str, text: str) -> None:
    """
    Builds the context for the agent based on the user's input.
    Drop context if last entry is older than 300s

    args:
        nick: The nickname of the user making the request.
        text: The text of the request.
    """
    
    global CONTEXT_TIMESTAMP
    if check_idle_context(300):
        CONTEXT.clear()
    CONTEXT.append({
        "content": f"{nick} says: {text}",
        "role": "user",
        "type": "message"
    })
    CONTEXT_TIMESTAMP = datetime.now().strftime('%m/%d/%y %H:%M:%S')
    if CONTEXT_DEBUG:
        with open("context.json",'w') as f:
            f.write(json.dumps(CONTEXT, indent=2))


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
    build_context(nick, text)
    result = await Runner.run(default_agent, CONTEXT)
    response = parse_response(result)
    return response
