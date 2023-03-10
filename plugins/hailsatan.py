from cloudbot import hook
import re


message = re.compile('666',re.IGNORECASE)


@hook.regex(message)
def hailsatan(match, nick, chan, db, notice):
    """no useful help txt"""
    return "https://public1235482.blob.core.windows.net/public/hailsatan.gif"