import requests
from requests import HTTPError, RequestException
from cloudbot import hook
from cloudbot.util.web import Pastebin, pastebins, ServiceHTTPError, ServiceError

class Mozilla(Pastebin):
    def __init__(self):
        super().__init__()
        self.url = "https://paste.mozilla.org/"

    def paste(self, data, ext):
        if isinstance(data, str):
            encoded = data.encode()
        else:
            encoded = data

        try:
            if ext == 'code':
                lexer = '_code'
            elif ext == 'md':
                lexer = '_markdown'
            else:
                lexer = '_text'

            form_data = {'format': 'json', 'content': encoded, 'lexer': lexer }
            r = requests.post(f'{self.url}/api/', data=form_data)
            r.raise_for_status()
        except HTTPError as e:
            r = e.response
            raise ServiceHTTPError(r.reason, r) from e
        except RequestException as e:
            raise ServiceError(e.request, "Connection error occurred") from e
        else:
            j = r.json()

            if r.status_code is requests.codes.ok:
                return f'{j['url']}'

            raise ServiceHTTPError(j['message'], r)

@hook.on_start()
def register():
    pastebins.register('mozilla', Mozilla())
@hook.on_stop()
def unregister():
    pastebins.remove('mozilla')
