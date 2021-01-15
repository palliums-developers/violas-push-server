import json, logging

from flask import Flask, request
from flask_cors import CORS

import FCMWrapper
from PGHandler import PGHandler
import Common
from PushLoop import PushLoop
from MessagePushQueue import MessagePushQueue

logging.basicConfig(filename = "PushServer.log", level = logging.DEBUG)

pgHandler = PGHandler()
pgHandler.init(Common.DB_URL)

queue = MessagePushQueue()
pl = PushLoop()
pl.start()

app = Flask(__name__)
CORS(app, resources = r"/*")

@app.route("/violas/push/message", methods = ["POST"])
def PushTransactionMessage():
    params = request.get_json()
    version = params.get("version")

    if version is None:
        return {"code": 1000}

    logging.debug(f"Get new request, version: {version}")
    queue.AddMessage(version)

    return {"code": 0}

@app.route("/violas/push/notice", methods = ["POST"])
def PushSystemNotice():
    params = request.get_json()
    noticeId = params.get("notice_id")


    return {"code": 0}
