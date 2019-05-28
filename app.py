import os
import requests
from flask import Flask, request, render_template, json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from redis import Redis

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

headers = {"Content-Type": "application/json"}
url = "https://openapi.zalo.me/v2.0/oa/message?access_token={}".format(access_token)
redis = Redis('localhost')


def get_zalo_history_key(user_id):
    return "ZALO::HISTORY::{}".format(user_id)

def get_zalo_invoice_key(user_id):
    return "ZALO::INVOICE::{}".format(user_id)


def check_customer_code(customer_code):
    base_api_url = os.environ["BASE_API_URL"]
    invoice_end_point_url = '/api/v2/invoice/?einvoice=true&partner_ref={}&limit=1'.format(customer_code)
    request_header = {
        'Content-Type': 'application/json',
        'app-version': '2.0.0'
    }
    user_login = 'admin'
    user_password = 'zaq1@2wsx345'
    data_login = {
        'email': user_login,
        'password': user_password
    }
    url_login_end_point = '/api/v2/users/login'
    res_login = requests.post(url=base_api_url + url_login_end_point, data=json.dumps(data_login),
                              headers=request_header).text
    token = json.loads(res_login).get('token')

    request_header['Authorization'] = token
    res_invoices = requests.get(url=base_api_url + invoice_end_point_url, headers=request_header).text
    invoices = json.loads(res_invoices)

    if res_invoices == '[]':
        return True
    elif 'message' in invoices:
        return False
    else:
        return True

def check_user_id(user_id):
    from models import Users
    result = []
    try:
        user = Users.query.filter_by(user_id=user_id)
        if user:
            for i in user:
                print(i.user_id)
                result.append(i.customer_code)
        return result
    except Exception as e:
        return result

def send_transaction_history(user_id, customer_code):

    base_api_url = os.environ['BASE_API_URL']
    invoice_end_point_url = '/api/v2/invoice/?einvoice=true&partner_ref={}&limit=3'.format(customer_code)
    request_header = {
        'Content-Type': 'application/json',
        'app-version': '2.0.0'
    }
    # Get token
    user_login = 'admin'
    user_password = 'zaq1@2wsx345'
    data_login = {
        'email': user_login,
        'password': user_password
    }
    url_login_end_point = '/api/v2/users/login'
    res_login = requests.post(url=base_api_url + url_login_end_point, data=json.dumps(data_login),
                              headers=request_header).text
    token = json.loads(res_login).get('token')

    request_header['Authorization'] = token
    res_invoices = requests.get(url=base_api_url + invoice_end_point_url, headers=request_header).text
    invoices = json.loads(res_invoices)
    text = ''
    str = ''
    name = ''
    if res_invoices == '[]':
        str = u'Hiện không có lịch sử dùng nước của khách hàng trong dữ liệu hệ thống.'
        text = str
    elif 'message' in invoices:
        str = u'Mã khách hàng của quý khách nhập không chính xác. Vui lòng nhập lại.'
        text = str
    else:
        for inv in invoices:
            state = u'Đã thanh toán' if inv['state'] == 'paid' else u"Chưa Thanh toán"
            str += u"Kỳ Hóa đơn: {}\nSố m3 tiêu thụ: {:,.0f}\nTổng tiền: {:,.0f} VNĐ\nTrạng thái: {} \n ".format(
                inv['period'],
                inv['volume_total'],
                inv['amount_total'], state)
            name = inv['partner']['name']
            str = str + "\n"
        text = u"Lich sử nước của \nKhách hàng: {}Mã khách hàng : {} là : {} ".format(name + "\n", customer_code,
                                                                                      "\n\n" + str)
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": text
        }
    }
    res = requests.post(url=url, data=json.dumps(data), headers=headers)
    return text

def send_invoice_pdf(user_id, customer_code):
    base_api_url = os.environ['BASE_API_URL']
    invoice_end_point_url = '/api/v2/invoice/?einvoice=true&partner_ref={}&limit=3'.format(customer_code)
    request_header = {
        'Content-Type': 'application/json',
        'app-version': '2.0.0'
    }
    # Get token
    user_login = 'admin'
    user_password = 'zaq1@2wsx345'
    data_login = {
        'email': user_login,
        'password': user_password
    }
    url_login_end_point = '/api/v2/users/login'
    res_login = requests.post(url=base_api_url + url_login_end_point, data=json.dumps(data_login),
                              headers=request_header).text
    token = json.loads(res_login).get('token')
    request_header['Authorization'] = token
    res_invoices = requests.get(url=base_api_url + invoice_end_point_url, headers=request_header).text
    invoices = json.loads(res_invoices)
    text = ''
    name = ''
    if res_invoices == '[]':
        link = u'Hiện không có hóa đơn của khách hang trong cơ sở dữ liệu'
        text = link
    elif 'message' in invoices:
        link = u'Mã khách hàng của quý khách nhập không chính xác. Vui lòng nhập lại.'
        text = link
    else:
        for inv in invoices:
            state = inv['state']
            if state != 'paid':
                continue
            period = inv['period']
            name = inv['partner']['name']
            link = "https://khachhang.ns3.vn/billing/pdf?einvoice_no={}&uid={}".format(inv['e_invoice']['einvoice_no'],
                                                                                       inv['e_invoice'][
                                                                                           'transaction_uuid'])
            text = text + u"Kỳ Hóa đơn: {}\nLink tải hóa đơn : {}".format(period, link) + "\n\n"
        text = u"Hóa đơn của \nKhách hàng: {}Mã khách hàng : {} là : {} ".format(name + "\n", customer_code,
                                                                                 "\n\n" + text)
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": text
        }
    }
    res = requests.post(url=url, data=json.dumps(data), headers=headers)
    return text



def send_error(user_id):
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": "Quý khách vui lòng nhập đăng ký để đăng ký thông tin tài khoản.\nNhập lich sử để tra cứu lịch sử dùng nước."
        }
    }
    res = requests.post(url=url, data=json.dumps(data), headers=headers)

def send_data(user_id, data):
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": data
        }
    }
    res = requests.post(url=url, data=json.dumps(data), headers=headers)



def send_register(user_id):
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "list",
                    "elements": [{
                        "title": "Công Ty Cổ Phần Sản Xuất Kinh Doanh Nước Sạch Số 3 Hà Nội",
                        "subtitle": u" Vui lòng thực hiện cấc chức năng sau.",
                        "image_url": "https://res.cloudinary.com/dnp-corp/image/upload/v1559051459/download.png",
                        "default_action": {
                            "type": "oa.open.url",
                            "url": "http://nuocsachso3hn.vn/"
                        }
                    },
                        {
                            "title": "Đăng ký tài khoản",
                            "subtitle": "website",
                            "image_url": "https://res.cloudinary.com/dnp-corp/image/upload/v1559051784/1.png",
                            "default_action": {
                                "type": "oa.open.url",
                                "url": "http://127.0.0.1:5500/?uuid={}".format(user_id)
                            }
                        },
                        {
                            "title": "Hướng dẫn đăng ký",
                            "subtitle": "Liên hệ",
                            "image_url": "https://res.cloudinary.com/dnp-corp/image/upload/v1559051787/2.jpg",
                            "default_action": {
                                "type": "oa.open.url",
                                "url": "http://127.0.0.1:5500/"
                            }
                        }]
                }
            }
        }
    }
    res = requests.post(url=url, data=json.dumps(data), headers=headers)


def invoice_customer_code(user_id, cmd):
    result = check_user_id(user_id)
    if cmd and cmd == 'lichsu':
        if redis.exists(get_zalo_history_key(user_id)):
            data = redis.get(get_zalo_history_key(user_id))
            send_data(user_id, data)
        else:
            if len(result) != 0:
                valueHistory= ""
                for cus in result:
                    valueHistory += send_transaction_history(user_id, cus) +"\n"
                redis.set(get_zalo_history_key(user_id), valueHistory)
            else:
                send_register(user_id)

    elif cmd and cmd == 'taihoadon':
        if redis.exists(get_zalo_invoice_key(user_id)):
            data = redis.get(get_zalo_invoice_key(user_id))
            send_data(user_id, data)
        else:
            if len(result) != 0:
                valueInvoice = ""
                for cus in result:
                    valueInvoice += send_invoice_pdf(user_id, cus) +"\n"
                redis.set(get_zalo_invoice_key(user_id), valueInvoice)
            else:
                send_register(user_id)
    else:
        send_error(user_id)




@app.route("/zalo", methods=["POST", "GET"])
def zalo():
    if request.method == 'GET':
        userid = request.args.get("fromuid")
        message = request.args.get("message","")

        if message not in "None":
            invoice_customer_code(userid, message)

    return os.environ['BASE_API_URL'] + '/api/v2/users/login'


@app.route('/')
def view_registered_user():
    uuid =  request.args.get("uuid")
    return render_template('user_registration.html', uuid=uuid)


@app.route('/register', methods=['POST'])
def register_user():
    from models import Users
    user_id = request.form.get('uuid')
    phone = request.form.get('phone')
    customer_code = request.form.get('customer_code')

    if check_customer_code(customer_code):
        try:
            result = Users.query.filter_by(user_id=user_id, customer_code=customer_code).first()
            if result:
                result.phone = phone
                result.create_date = str(datetime.today().strftime('%d-%m-%Y'))
                db.session.merge(result)
                db.session.commit()
            else:
                user = Users(
                    user_id=user_id,
                    phone=phone,
                    customer_code=customer_code,
                    create_date=str(datetime.today().strftime('%d-%m-%Y'))
                )
                db.session.add(user)
                db.session.commit()
                redis.delete(get_zalo_invoice_key(user_id))
                redis.delete(get_zalo_history_key(user_id))

            return render_template('user_confirmation.html', phone=phone, customer_code=customer_code)
        except Exception as e:
            return (str(e))
    else:
        return "Sai mã khách hàng"


if __name__ == '__main__':
    app.run(port=5500)

# export APP_SETTINGS="config.DevelopmentConfig"
# export DATABASE_URL="postgresql://giaphong:123gnohp123@localhost:5432/chatbot_web"
# export BASE_API_URL="http://192.168.1.33:5000"
