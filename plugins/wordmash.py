import random
import requests
from sqlalchemy import Table, Column, String, Integer
from sqlalchemy.sql import func, insert, update
from cloudbot.util import database
from cloudbot import hook

RETRY = [
    "Better luck next time !",
    "You can do it",
    "... really ?",
    "lmao"
]

words = Table(
    'wordmash_words',
    database.metadata,
    Column('word', String)
)

scores = Table(
    'wordmash_score',
    database.metadata,
    Column('username', String),
    Column('score', Integer)
)

current_mash = ""
current_word = ""

def get_definition(word: str) -> str:
    """
    This method fetches a word definition from the Free Dictionnary API

    Args:
        word (str): Word to be defined 

    Returns:
        str: The word definition
    """
    resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
    if resp.status_code != 200:
        return "No definition for this word"
    return resp.json()[0]["meanings"][0]["definitions"][0]["definition"]

def bump_nick_score(nick: str) -> int:
    """
    Increments the user score in database
    Args:
        nick (str): User nickname
    
    Returns:
        int: The user new score
    """
    user_score = scores.select(scores.c.username == nick).limit(1).execute().first()
    if not user_score:
        insert(scores).values(username=nick, score=1).compile().execute()
        return 1
    if nick == "esses":
         update(scores).where(scores.c.username == nick).values(score=user_score.score-1).execute()
         return user_score.score - 1
    else:
        update(scores).where(scores.c.username == nick).values(score=user_score.score+1).execute()
        return user_score.score + 1

def serve_new_mash() -> str:
    """
    Serve a new wordmash

    Returns:
        str: Bot message serving new wordmash
    """
    global current_word
    global current_mash
    current_word = words.select().order_by(func.random()).execute().first()['word']
    current_mash = ''.join(random.sample(current_word, len(current_word)))
    return f"A new mash is served. Enjoy your \x0309{current_mash}\x03"
    

@hook.command("wordmash", autohelp=False)
def wordmash(nick: str, text: str) -> str:
    """
    This command can:
     - Create a wordmash
     - Return the current wordmash
     - Submit a wordmash
     Returns:
        str: Bot Message
    """
    global current_word
    global current_mash
    if text != "" and current_mash != "":
        if text == current_word:
            return [
                f"Good job! \x0309{current_word}\x03: {get_definition(current_word)}",
                f"You gain an internet point, making your total \x0308{bump_nick_score(nick)}\x03",
                serve_new_mash()
            ]
        else:
            return random.choice(RETRY)
    if current_mash != "":
        return f"The current mash is: \x0309{current_mash}\x03"
    return serve_new_mash()

@hook.command("wordmash_reset", autohelp=False)
def reset_wordmash() -> list[str]:
    """
    This command allows for a new wordmash to be served
    Returns:
       []str:  Bot Message
    """
    global current_word
    return [
        f"Reset ! The word was \x0309{current_word}\x03: {get_definition(current_word)}",
        serve_new_mash()
    ]

@hook.command("wordmash_scores", autohelp=False)
def wordmash_scores(chan) -> str:
    """
    This command returns the top 10 user scores
    Returns:
        str: Bot Message
    """
    user_scores = scores.select().order_by(scores.c.score.desc()).limit(10).execute()
    out = f"Word mash scores in {chan}: "
    for nick, score in user_scores:
        out += f"\x02{nick[:1] + ' ' + nick[1:]}\x02: {score} • "
    return out

@hook.command("wordmash_hint", autohelp=False)
def wordmash_hint() -> str:
    """
    This command gives the definition of the wordmash as an hint
    to help players find the word
    Returns:
        str: Bot Message
    """
    global current_word
    return f"\x02Hint:\x02 {get_definition(current_word)}"
