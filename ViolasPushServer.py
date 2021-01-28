import json, logging

from flask import Flask, request
from flask_cors import CORS

from FCMWrapper import FCMWrapper
from PGHandler import PGHandler
import Common
from PushLoop import PushLoop
from MessagePushQueue import MessagePushQueue

logging.basicConfig(filename = "PushServer.log", level = logging.DEBUG)

pgHandler = PGHandler()
pgHandler.init(Common.DB_URL)

fcm = FCMWrapper()
fcm.init(Common.CERT_PATH)

queue = MessagePushQueue()
pl = PushLoop()
pl.start()

app = Flask(__name__)
CORS(app, resources = r"/*")

@app.route("/violas/push/message", methods = ["POST"])
def PushTransactionMessage():
    params = request.get_json()
    data = {
        "service": params.get("service"),
        "content": params.get("version")
    }

    logging.debug(f"Get new request, data: {data}")
    queue.AddMessage(data)

    return {"code": 0}

@app.route("/violas/push/notification", methods = ["POST"])
def PushSystemNotice():
    params = request.get_json()
    data = {
        "service": params.get("service"),
        "content": params.get("id")
    }

    logging.debug(f"Get new request, data:{data}")
    queue.AddMessage(data)

    return {"code": 0}

@app.route("/violas/push/subscribe/topic", methods = ["POST"])
def SubscribeTopic():
    params = request.get_json()
    topic = params.get("topic")
    token = params.get("token")

    fcm.SubscribeToTopic(topic, token)

    return {"code": 0}
