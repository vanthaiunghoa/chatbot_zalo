from flask import Flask, render_template, request
from chatterbot import ChatBot


app = Flask(__name__)

crm_bot = ChatBot("CRMBOT",
                  logic_adapters=[
                      {
                          'import_path': 'crm_adapter.CrmAdapter'
                      }],
                  storage_adapter="chatterbot.storage.SQLStorageAdapter")


@app.route("/zalo", methods=["POST", "GET"])
def zalo():
    if request.method == 'GET':
        userid = request.args.get("fromuid")
        message = request.args.get("message")
        userText  = '{}|{}'.format(userid, message)
        res = crm_bot.get_response(str(userText))
        print(res)
    return 'Ok'


if __name__ == "__main__":
    app.run()
