# -*- coding: utf-8 -*-
"""HTTP odjemalec za GET /game/<GAME_ID>; deluje s pycurl ali urllib."""
import json
from io import BytesIO

try:
    import ujson as _json
except ImportError:
    _json = json

try:
    import pycurl as _pycurl
except ImportError:
    _pycurl = None


class Connection(object):
    def __init__(self, server_url, game_id=None, timeout=1.5):
        base = str(server_url).rstrip("/")
        if "/game/" in base:
            self.url = base if game_id is None else base.rstrip("/") + "/" + str(game_id)
        else:
            if not game_id or str(game_id) == "CHANGE_ME":
                raise ValueError("Nastavite GAME_ID v starter_code/config.py")
            self.url = base + "/game/" + str(game_id)
        self.timeout = float(timeout)
        self.last_error = None
        self._curl = None
        self._buffer = BytesIO()
        if _pycurl is not None:
            self._curl = _pycurl.Curl()
            self._curl.setopt(_pycurl.URL, self.url)
            self._curl.setopt(_pycurl.CONNECTTIMEOUT_MS, int(self.timeout * 1000))
            self._curl.setopt(_pycurl.TIMEOUT_MS, int(self.timeout * 1000))
            self._curl.setopt(_pycurl.NOSIGNAL, 1)
            self._curl.setopt(_pycurl.WRITEDATA, self._buffer)

    def request(self, debug=False):
        self.last_error = None
        try:
            if self._curl is not None:
                self._buffer.seek(0)
                self._buffer.truncate(0)
                self._curl.perform()
                code = self._curl.getinfo(_pycurl.RESPONSE_CODE)
                if code < 200 or code >= 300:
                    raise IOError("HTTP status {}".format(code))
                payload = self._buffer.getvalue().decode("utf-8")
            else:
                # Fallback brez odvisnosti za testiranje na računalniku.
                try:
                    from urllib.request import urlopen
                except ImportError:  # pragma: no cover - Python 2 združljivost
                    from urllib2 import urlopen
                response = urlopen(self.url, timeout=self.timeout)
                try:
                    payload = response.read().decode("utf-8")
                finally:
                    response.close()
            return _json.loads(payload)
        except Exception as err:
            self.last_error = str(err)
            if debug:
                print("Napaka pri branju igralnega strežnika: {}".format(err))
            return None

    def test_delay(self, num_iters=5):
        import time
        started = time.time()
        successful = 0
        for _ in range(max(1, int(num_iters))):
            if self.request() is not None:
                successful += 1
        elapsed = time.time() - started
        return elapsed / float(max(1, int(num_iters))), successful

    def close(self):
        if self._curl is not None:
            try:
                self._curl.close()
            except Exception:
                pass
            self._curl = None
