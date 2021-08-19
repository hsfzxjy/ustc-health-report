import os
import sys
import requests
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
        ("is_inschool", "input", "7"),
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


def login(session: requests.Session, username: str, password: str):
    response = session.post(
        "https://passport.ustc.edu.cn/login",
        data={
            "model": "uplogin.jsp",
            "service": "https://weixine.ustc.edu.cn/2020/caslogin",
            "warn": "",
            "showCode": "",
            "username": username,
            "password": password,
            "button": "",
        },
    )
    return response


def report_health(response: requests.Response):
    root = document_fromstring(response.text)
    payload = _extract_form_values(root)
    # print(payload)
    return session.post("https://weixine.ustc.edu.cn/2020/daliy_report", data=payload)


if __name__ == "__main__":
    IDENT = os.getenv("IDENT")
    session = requests.Session()
    r = login(session, *IDENT.split(":"))
    # print("logined")
    r = report_health(r)
    # print(r.status_code)
    if r.status_code != 200 or "上报成功" not in r.text:
        # print(r.text)
        print('error')
        sys.exit(1)
