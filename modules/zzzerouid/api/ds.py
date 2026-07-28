import hashlib
import json
import random
import string
import time


MYS_VERSION = "2.102.1"

_SALTS = {
    "2.102.1": {
        "K2": "lX8m5VO5at5JG7hR8hzqFwzyL5aB1tYo",
        "LK2": "yBh10ikxtLPoIhgwgPZSv5dmfaOTSJ6a",
        "22": "t0qEgfub6cvueAPgR5m9aQWWVciEer7v",
        "25": "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs",
    },
    "os": "6cqshh5dhw73bzxn20oexa9k516chk7s",
    "PD": "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS",
}


def md5(text: str) -> str:
    m = hashlib.md5()
    m.update(text.encode())
    return m.hexdigest()


def get_ds_token(q: str = "", b=None, salt_id: str = "25") -> str:
    salt = _SALTS[MYS_VERSION][salt_id]
    br = json.dumps(b) if b else ""
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5(f"salt={salt}&t={t}&r={r}&b={br}&q={q}")
    return f"{t},{r},{c}"


def get_web_ds_token(web: bool = False) -> str:
    salt = _SALTS[MYS_VERSION]["LK2"] if web else _SALTS[MYS_VERSION]["K2"]
    return _random_str_ds(salt)


def _random_str_ds(
    salt: str,
    sets: str = string.ascii_lowercase + string.digits,
    with_body: bool = False,
    q: str = "",
    b=None,
) -> str:
    i = str(int(time.time()))
    r = "".join(random.sample(sets, 6))
    s = f"salt={salt}&t={i}&r={r}"
    if with_body:
        s += f"&b={json.dumps(b) if b else ''}&q={q}"
    c = md5(s)
    return f"{i},{r},{c}"


def generate_os_ds(salt: str = "") -> str:
    return _random_str_ds(salt or _SALTS["os"], sets=string.ascii_letters)


def generate_passport_ds(q: str = "", b=None) -> str:
    return _random_str_ds(_SALTS["PD"], string.ascii_letters, True, q, b)


def random_hex(length: int) -> str:
    return "".join(random.choice(string.hexdigits) for _ in range(length))


def random_text(num: int) -> str:
    return "".join(random.sample(string.ascii_letters + string.digits, num))
