import csv
import hashlib
import json
import sys

import pandas as pd
import requests
import datetime
import time
from urllib.parse import urlencode
import os

# 请求头
headers = {
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x18002230) NetType/WIFI Language/zh_CN",
    "Content-Type": "application/x-www-form-urlencoded",
    # "Content-Length": "2",
    # "Host": "student.wozaixiaoyuan.com",
    "Accept-Language": "en-us,en",
    # "host": "student.wozaixiaoyuan.com",
    "Accept": "application/json, text/plain, */*"
}

filename = "jwsession"


def encryption(user_name):
    user_id = str(user_name)[:2] + "***" + str(user_name)[-4:]

    return user_id


def write_csv(filename, data_list):
    keys = data_list[0].keys()
    print(f"开始写入{filename}")
    with open(f'{filename}.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(keys)
        for w in data_list:
            writer.writerow(w.values())

    print(f"写入{filename}完成\n")


# 定义用密码登录的函数
def login(user_name, pass_word):
    print("使用登录模式获取JWSESSION")
    # 登陆接口
    loginUrl = "https://student.wozaixiaoyuan.com/basicinfo/mobile/login/username"
    url = loginUrl + "?username=" + str(user_name) + "&password=" + str(pass_word)
    session = requests.session()

    # 请求体（必须有） body = "{}"
    body = "{}"

    response = session.post(url=url, data=body, headers=headers)
    res = json.loads(response.text)

    if res["code"] == 0:
        # 登录成功获取JWSESSION
        new_jwsession = response.headers['JWSESSION']
        print("登录成功，自动保存，new_jwsession-->", new_jwsession)

        return new_jwsession
    else:
        print("登录失败，结果-->", res)
        return False


def reset(user_name, pass_word):
    jwsession_info = pd.read_csv(f"{filename}.csv")
    jwsession = jwsession_info[jwsession_info["username"] == encryption(user_name)]["JWSESSION"].values[0]

    headers_reset = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": "https://gw.wozaixiaoyuan.com/h5/mobile/basicinfo/index/my/changePassword",
        "Host": "gw.wozaixiaoyuan.com",
        "User-Agent": "Mozilla/5.0 (iPad; CPU OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.23(0x1800172f) NetType/WIFI Language/zh_CN miniProgram/wxce6d08f781975d91",
        "Connection": "keep-alive",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "JWSESSION": jwsession,
        "Cookie": f"JWSESSION={jwsession}"
    }
    reset_url = f"https://gw.wozaixiaoyuan.com/basicinfo/mobile/my/changePassword?newPassword={pass_word}&oldPassword={pass_word}&code="
    res = requests.post(url=reset_url, headers=headers_reset)

    if res.json()["code"] == 0:
        new_jwsession = res.headers["JWSESSION"]
        print("密码修改成功，成功获取JWSESSION，自动保存，new_jwsession-->", new_jwsession)

        return new_jwsession
    else:
        print("修改密码失败，结果-->", res)
        return False


def get_location(latitude, longitude):
    url = "https://apis.map.qq.com/ws/geocoder/v1/?key=A3YBZ-NC5RU-MFYVV-BOHND-RO3OT-ABFCR&location={},{}".format(
        latitude, longitude)
    res = requests.get(url)
    resList = res.json()

    if resList["status"] == 0:
        result = resList["result"]
        address_component = result["address_component"]
        address_reference = result["address_reference"]
        ad_info = result["ad_info"]

        city = address_component["city"]
        district = address_component["district"]
        province = address_component["province"]
        township = address_reference["town"]["title"]
        street = address_component["street"]
        adcode = ad_info["adcode"]
        towncode = address_reference["town"]["id"]
        citycode = ad_info["city_code"]
        nationcode = ad_info["nation_code"]
        streetcode = address_reference["street"]["id"]

        locationList = [city, district, province, township, street, adcode, towncode, citycode, nationcode,
                        streetcode]

        return locationList


def get_list(h):
    url = "https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs?page=1&size=1"
    res = requests.get(url, headers=h)
    res_text = res.json()["data"][0]

    area_json = res_text["areaList"][0]
    sign_id = res_text["signId"]
    item_id = res_text["id"]
    school_id = res_text["schoolId"]

    return area_json, sign_id, item_id, school_id


class Do:
    def __init__(self):
        self.headers = headers
        # 请求体（必须有） self.body = "{}"
        self.body = "{}"
        self.user_list = []

    def get_JWSESSION(self, username, password):
        lo = login(username, password)
        if lo:
            self.headers["JWSESSION"] = lo
            row = {
                "username": encryption(username),
                "JWSESSION": lo
            }
            self.user_list.append(row)
        else:
            print("登陆失败，使用上一次的JWSESSION登录\n")
            self.headers["JWSESSION"] = reset(username, password)
            row = {
                "username": encryption(username),
                "JWSESSION": self.headers["JWSESSION"]
            }
            self.user_list.append(row)

    def punch(self):
        # 获取位置信息
        location_list = get_location(latitude, longitude)

        # 获取签到列表信息
        area_json, sign_id, item_id, school_id = get_list(self.headers)

        areaJSON = {
            "type": 0,
            "circle": {
                "latitude": area_json["latitude"],
                "longitude": area_json["longitude"],
                "radius": area_json["radius"]
            },
            "id": area_json["id"],
            "name": area_json["name"]
        }

        # 打卡表单构建
        data = {
            "towncode": location_list[6],
            "longitude": longitude,  # 经度
            "province": location_list[2],
            "latitude": latitude,  # 维度
            "streetcode": location_list[9],
            "street": location_list[4],
            "areaJSON": str(areaJSON),
            "citycode": location_list[7],
            "city": location_list[0],
            "nationcode": location_list[8],
            "adcode": location_list[5],
            "district": location_list[1],
            "township": location_list[3],
            "country": "中国",
            "inArea": 1,
        }

        # print(data)

        url = f"https://gw.wozaixiaoyuan.com/sign/mobile/receive/doSignByArea?id={item_id}&schoolId={school_id}&signId={sign_id}"
        # print("url-->", url)

        # 请求头
        headers_post = {"Connection": "keep-alive",
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x18002230) NetType/WIFI Language/zh_CN",
                        "Content-Type": "application/json",
                        "Accept-Encoding": "gzip,compress,br,deflate",
                        "Host": "gw.wozaixiaoyuan.com",
                        "token": "",
                        # "Referer": "https://servicewechat.com/wxce6d08f781975d91/189/page-frame.html",
                        "JWSESSION": self.headers["JWSESSION"]
                        }

        res = requests.post(url=url, headers=headers_post,
                            json=data)  # 健康打卡提交
        res_text = res.json()
        print("res-->", res_text)
        if res_text["code"] == 0:
            print("打卡成功")
        elif res_text["code"] == 1:
            print("message", res_text["message"])
        else:
            print("打卡失败")


if __name__ == "__main__":
    user_list = os.environ.get('USER', '').split('\n')
    info = os.environ.get('INFO', '').split('\n')
    latitude = info[0]
    longitude = info[1]

    password = 123456789

    uses = Do()
    for i in user_list:
        user_number = i.split(",")[0]
        user_name = i.split(",")[1]
        print(f"---------用户：{encryption(user_number)}:{user_name}开始打卡------------")
        # weekday = datetime.datetime.now().weekday() + 1
        print(f"现在是{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}")
        uses.get_JWSESSION(i, password)
        # 星期天才打卡，其他时间更新JWSESSION
        # if weekday == 7:
        uses.punch()

        time.sleep(1)
    print("---------------------end-------------------------")
    write_csv(filename, uses.user_list)
