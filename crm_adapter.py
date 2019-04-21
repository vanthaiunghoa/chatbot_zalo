from chatterbot.logic import LogicAdapter
import re
from redis import Redis
import requests
from flask import json

pattern_makh = re.compile("^.*2[0-9]{9}$")

redis = Redis('localhost')
access_token = "dk8HLjdGNtULvXzLrzrGVP7d7bpSoWL_-Rai5zAD4MVmpLKVog96JCVWSWBWZ7ugtifn2zFvNodna4vKqy5e7VY0BLo-pNOE_gGtQVoLCX_i-pv7hB8a4QpOEK-Qhtq9l9Gp897uFsVGbWybbEC33Qca7MoUnXagWfeNVxFWK2MTfcTGXl1m4i6rCJgDy0CTbhiCDAIC3co3kamAmDrDIDVdSnV6a7H3v-HuQiUaDadXzpSQnDabU_IG41tI-nOrwijKRjAcIGR3bMbGT0Ds4TdFL74"
headers = {"Content-Type": "application/json"}
url = "https://openapi.zalo.me/v2.0/oa/message?access_token={}".format(access_token)


def get_zalo_key(user_id):
    return "ZALO::USER::{}".format(user_id)


def taihoadon(customer_code):
    return "link tai hoa don"


def lichsusudung(customer_code):
    return "Lich su su dung"

def send_history(user_id , customer_code):

    str = "TTCT ve lich su cua khach hang"
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": u"Lịch sử dùng nước gần nhất của Khách hàng mã {} là {} ".format(customer_code, str)
        }
    }
    res = requests.post(url= url, data = json.dumps(data), headers = headers)

def send_register(user_id):
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": u"Xin chào, Vui lòng nhập mã khách hàng"
        }
    }
    res = requests.post(url=url, data=json.dumps(data), headers=headers)


supported_commands = {
    '#taihoadon': taihoadon,
    '#lichsusudung': lichsusudung,
}


class CrmAdapter(LogicAdapter):

    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement

        # if match maKH -> set ma KH vao redis, return huong dan tra cuu
        # if match command -> check ma kh -> return ket qua
        # else error: return nhap ma khach hang
        # makh = "211017416"


        confidence = 1
        try:
            commands = supported_commands.keys()
            userid, cmd = input_statement.text.split('|')

            if cmd in commands:
                if redis.exists(get_zalo_key(userid)):
                    confidence = 1
                else:
                    confidence = 0
            elif cmd and "21" in cmd:
                redis.set(get_zalo_key(userid), cmd)
                confidence = 1
            else:
                confidence = 2
        except :
            confidence = 2



        if confidence == 1:
            response_statement = Statement(text='Chi tiết thông tin', confidence=confidence)
            send_history(userid, cmd)
        elif confidence == 0:
            response_statement = Statement(text='Xin lỗi, xin vui lòng nhập mã khách hàng của bạn')
            send_register(userid)
        elif confidence == 2:
            response_statement = Statement(text='Dữ liệu không hợp lệ. Vui Lòng nhập lại', confidence=confidence)
            send_register(userid)
        return response_statement

