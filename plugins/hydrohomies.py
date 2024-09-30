from cloudbot import hook
import re
import random

#message = re.compile('^.*?\\bhydro\\b(\S*\s){0,4}\\bhomie\\b.*?$',re.IGNORECASE)
message = re.compile('^.*?\\bhydr\\S.*?$$',re.IGNORECASE)
message2 = re.compile('[0-9]',re.IGNORECASE)


@hook.regex(message)
def hydrohomie(match, nick, chan, db, notice):
    """no useful help txt"""
    homies = ["HYDRO HOMIES", "Hippies Hydrate", "CHUG! CHUG! CHUG!", "💦"]
    return (random.choice(homies))

