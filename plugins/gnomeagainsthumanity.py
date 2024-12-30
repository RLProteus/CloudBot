import os
import codecs
import json
import asyncio
import random
import re
from typing import Dict, List

from cloudbot import hook

gnomecards: Dict[str, List[str]] = {}
import re
import time


@hook.on_start()
def shuffle_deck(bot):
    gnomecards.clear()
    with open((bot.data_path / "gnomecards.json"), encoding="utf-8") as f:
        gnomecards.update(json.load(f))

    global gnomecards
    with codecs.open(os.path.join(bot.data_dir, "gnomecards.json"), encoding="utf-8") as f:
        gnomecards = json.load(f)



@hook.command("cah")
def CAHwhitecard(text):
    """<text> - Submit text to be used as a CAH whitecard"""
    return random.choice(gnomecards["black"]).format(text)
@hook.command('cahw')
def CAHwhitecard(text, message):
    '''Submit text to be used as a CAH whitecard'''
    CardText = text.strip()
    return random.choice(gnomecards['black']).format(text)


@hook.command("cahb")
def CAHblackcard(text):
    """<text> - Submit text with _ for the bot to fill in the rest. You can submit text with multiple _"""
@hook.command('cahb')
def CAHblackcard(text, message):
    '''Submit text with _ for the bot to fill in the rest. You can submit text with multiple _'''
    CardText = text.strip()

    def blankfiller(matchobj):
        return random.choice(gnomecards["white"])

    out = re.sub(r"\b_\b", blankfiller, CardText)
    return out

@hook.command(autohelp=False)
def CAH(text, message):
    '''Submit text to be used as a CAH whitecard'''
    CardText = text.strip()

    def blankfiller(matchobj):
        return random.choice(gnomecards['white'])
    def blackcard():
        return random.choice(gnomecards['black'])
    blackcardstr = blackcard()
    blankfillerstr = blankfiller('i')
    out = re.sub('\{\}', blankfiller, blackcardstr)
    #out = whitecard()
    #out = blankfillerstr
    return out

@hook.command('cahwtest', autohelp=False, permissions=["op"])
def CAHwhitecardtest(text, message, db):
    '''Submit text to be used as a CAH whitecard'''
    CardText = text.strip()
    
    times = time.time() - 86400
    results = db.execute("select name from seen_user where chan = :chan and time > :time", {"chan": "##msp", "time": times}).fetchall()
    if not results or len(results) < 2:
        return "something went wrong"
    # Make sure the list of people is unique
    people = list(set(row[0] for row in results))
    random.shuffle(people)
    person1, person2 = people[:2]
    variables = {
        'user1': person1,
        'user2': person2,
    }
    #generator = TextGenerator(hookups['templates'], hookups['parts'], variables=variables)
    #return generator.generate_string()
    return random.choice(gnomecards['black']).format(person1)

@hook.command('cahbtest', autohelp=False, permissions=["op"])
def CAHblackcardtest(text, message, db):
    '''Submit text with _ for the bot to fill in the rest. You can submit text with multiple _'''
    CardText = text.strip()
    times = time.time() - 86400
    results = db.execute("select name from seen_user where chan = :chan and time > :time", {"chan": "##msp", "time": times}).fetchall()
    def blankfiller(matchobj):
            
            if not results or len(results) < 2:
                return "something went wrong"
            # Make sure the list of people is unique
            people = list(set(row[0] for row in results))
            random.shuffle(people)
            person1, person2 = people[:2]
            variables = {
                'user1': person1,
                'user2': person2,
            }
            card = random.choice(gnomecards['white'])            
            return random.choice([person1, card])

    out = re.sub(r'\b_\b', blankfiller, CardText)
    return out