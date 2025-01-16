import json
import os
import re
import time
from base64 import b64encode

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


# 请求头
# headers = {
#     # "Accept-Encoding": "gzip, deflate, br",
#     "Connection": "keep-alive",
#     "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x18002230) NetType/WIFI Language/zh_CN",
#     "Content-Type": "application/x-www-form-urlencoded",
#     "Accept-Language": "en-us,en",
#     "Accept": "application/json, text/plain, */*",
# }


def encryption(user_name):
    user_id = str(user_name)[:2] + "***" + str(user_name)[-4:]

    return user_id


def encrypt(password, username):
    key = (str(username) + "0000000000000000")[:16].encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded_text = pad(str(password).encode('utf-8'), AES.block_size)
    encrypted_text = cipher.encrypt(padded_text)
    return b64encode(encrypted_text).decode('utf-8')


class Do:
    def __init__(self):
        # 请求头
        self.headers = {
            # "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x18002230) NetType/WIFI Language/zh_CN",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "en-us,en",
            "Accept": "application/json, text/plain, */*",
        }
        # 请求体（必须有） self.body = "{}"
        self.body = "{}"
        self.user_list = []
        self.latitude = info[0]
        self.longitude = info[1]

    def get_location(self):
        # old_api = A3YBZ-NC5RU-MFYVV-BOHND-RO3OT-ABFCR
        url = "https://apis.map.qq.com/ws/geocoder/v1/?key=2DUBZ-HUMLU-3GAVO-GQJPZ-HMQDV-O4F5E&location={},{}".format(
            self.latitude, self.longitude)
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

    def get_list(self):
        url = "https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs?page=1&size=1"
        res = requests.get(url, headers=self.headers)
        res_text = res.json()["data"][0]
        print("标题：", res_text["signContext"])

        area_json = res_text["areaList"][0]

        sign_id = res_text["signId"]
        item_id = res_text["id"]
        school_id = res_text["schoolId"]

        return area_json, sign_id, item_id, school_id

    def login(self, user_name, pass_word):
        print("使用登录模式获取JWSESSION")
        # 登陆接口
        loginUrl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"

        pass_word_encrypt = encrypt(password=pass_word, username=user_name)

        url = loginUrl + "?username=" + str(user_name) + "&password=" + str(pass_word_encrypt) + "&schoolId=253"
        session = requests.session()

        # 请求体（必须有） body = "{}"
        body = "{}"

        response = session.post(url=url, data=body, headers=self.headers)

        res = json.loads(response.text)

        if res["code"] == 0:
            # 登录成功获取JWSESSION
            # 定义正则表达式
            pattern = r'(?<=JWSESSION=).+?(?=;)'
            # 使用正则表达式匹配两个特定字符之间的字符
            new_jwsession = re.findall(pattern, response.headers["Set-Cookie"])[0]

            print("登录成功")
            return new_jwsession
        else:
            print("登录失败，结果-->", res)
            return False

    def get_JWSESSION(self, username, password):
        lo = self.login(username, password)
        if lo:
            self.headers["JWSESSION"] = lo
            row = {
                "username": encryption(username),
                "JWSESSION": lo
            }
            self.user_list.append(row)

    def punch(self):
        # 获取位置信息
        location_list = self.get_location()

        # 获取签到列表信息
        area_json, sign_id, item_id, school_id = self.get_list()

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
            "longitude": self.longitude,  # 经度
            "province": location_list[2],
            "latitude": self.latitude,  # 维度
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

        url = f"https://gw.wozaixiaoyuan.com/sign/mobile/receive/doSignByArea?id={item_id}&schoolId={school_id}&signId={sign_id}"

        # 请求头
        headers_post = {"Connection": "keep-alive",
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x18002230) NetType/WIFI Language/zh_CN",
                        "Content-Type": "application/json",
                        "Accept-Encoding": "gzip,compress,br,deflate",
                        "Host": "gw.wozaixiaoyuan.com",
                        "token": "",
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

    password = 123456789

    for i in user_list:
        try:
            user_number = i.split(",")[0]
            user_name = i.split(",")[1]

            print(f"---------用户：{encryption(user_number)}:{user_name}开始打卡------------")
            print(f"现在是{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}")
            uses = Do()
            uses.get_JWSESSION(user_number, password)
            print(uses.headers["JWSESSION"])
            uses.punch()

            time.sleep(1)
        except Exception as e:
            print(f"用户：{encryption(user_number)}:{user_name}打卡失败,跳过")

    print("---------------------end-------------------------")
