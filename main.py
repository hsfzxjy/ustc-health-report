import os
import sys
import requests
import datetime
from lxml.html import document_fromstring


def _get_value(form, name: str, pattern: str):
    pattern = {
        "input": "input[name={}]",
        "checked-input": "input[name={}][checked]",
        "textarea": "textarea[name={}]",
        "select": "select[name={}]",
        "hidden": "input#{}_hidden",
    }[pattern]
    elements = form.cssselect(pattern.format(name))
    if not elements:
        raise RuntimeError(f"{name} {pattern}")
        return None
    return elements[0].value


def _extract_form_values(root):
    form: Element = root.cssselect("#daliy-report form")[0]
    payload = {}
    for name, pattern, default in [
        ("_token", "input", ""),
        ("now_address", "checked-input", "1"),
        ("gps_now_address", "input", ""),
        ("gps_province", "input", ""),
        ("now_province", "hidden", "340000"),
        ("gps_city", "input", ""),
        ("now_city", "hidden", "340100"),
        ("gps_country", "input", ""),
        ("now_country", "hidden", ""),
        ("now_detail", "textarea", ""),
        ("is_inschool", "input", "4"),
        ("body_condition", "select", "1"),
        ("body_condition_detail", "textarea", ""),
        ("now_status", "select", "1"),
        ("now_status_detail", "textarea", ""),
        ("has_fever", "checked-input", "0"),
        ("last_touch_sars", "checked-input", "0"),
        ("last_touch_sars_date", "input", ""),
        ("last_touch_sars_detail", "textarea", ""),
        ("is_danger", "input", "0"),
        ("is_goto_danger", "input", "0"),
        ("other_detail", "textarea", ""),
        ("jinji_lxr", "input", "王刚"),
        ("jinji_guanxi", "input", "父子"),
        ("jiji_mobile", "input", "13923456789"),
    ]:
        payload[name] = _get_value(form, name, pattern) or default
    return payload


def _another_extract_form_values(root):
    form: Element = root.cssselect("#daliy-report form")[0]
    payload = {}
    for name, pattern, default in [
        ("_token", "input", ""),
        ("name", "input", ""),
        ("zjhm", "input", ""),
        ("dep_mame", "input", ""),
        ("start_date", "input", ""),
        ("end_date", "input", ""),
    ]:
        payload[name] = _get_value(form, name, pattern) or default
    return payload

def get_validatecode(session: requests.Session) -> str:
    import re
    import pytesseract
    from PIL import Image
    from io import BytesIO

    for attempts in range(20):
        response = session.get(
            "https://passport.ustc.edu.cn/validatecode.jsp?type=login"
        )
        stream = BytesIO(response.content)
        image = Image.open(stream)
        text = pytesseract.image_to_string(image)
        codes = re.findall(r"\d{4}", text)
        if len(codes) == 1:
            break
    return codes[0]


def login(session: requests.Session, username: str, password: str):
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Origin": "https://passport.ustc.edu.cn",
            "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    session.cookies.set("lang", "zh")
    response = session.get(
        "https://weixine.ustc.edu.cn/2020/caslogin",
        headers={"Referer": "https://weixine.ustc.edu.cn/2020/login"},
    )
    root = document_fromstring(response.text)
    input = root.cssselect("input[name=CAS_LT]")
    CAS_LT = input[0].value

    response = session.post(
        "https://passport.ustc.edu.cn/login",
        data={
            "model": "uplogin.jsp",
            "service": "https://weixine.ustc.edu.cn/2020/caslogin",
            "CAS_LT": CAS_LT,
            "warn": "",
            "showCode": "1",
            "username": username,
            "password": password,
            "button": "",
            "LT": get_validatecode(session),
        },
        headers={
            "Referer": "https://passport.ustc.edu.cn/login?service=https://weixine.ustc.edu.cn/2020/caslogin",
        },
        allow_redirects=True,
    )
    return response


def report_health(response: requests.Response):
    root = document_fromstring(response.text)
    payload = _extract_form_values(root)
    response = session.post("https://weixine.ustc.edu.cn/2020/daliy_report", data=payload)
    print(r.status_code)
    if response.status_code != 200 or "上报成功" not in response.text:
        print("error")
        sys.exit(1)
    else:
        print("Daily report OK")
    response = session.get(
        "https://weixine.ustc.edu.cn/2020/apply/daliy",
        headers={"Referer": "https://weixine.ustc.edu.cn/2020/daliy_report"}
    )
    return response

def report_out(response: requests.Response):
    today = datetime.datetime.now().weekday() + 1
    if(today == 5):
        print("Time for out!")
        root = document_fromstring(response.text)
        payload = _another_extract_form_values(root)
        #print(payload)
        response = session.post("https://weixine.ustc.edu.cn/2020/apply/daliy/post", data=payload)
        print(response.status_code)
        if response.status_code != 200:
            print("error")
            sys.exit(1)
        else:
            print("Out report OK")
        return response
    else:
        print("Not today... But OK!")
        return response
if __name__ == "__main__":
    IDENT = os.getenv("IDENT")
    session = requests.Session()
    r = login(session, *IDENT.split(":"))
    print("logined")
    r = report_health(r)
    if os.getenv('REPORT_OUT'):
        r = report_out(r)
