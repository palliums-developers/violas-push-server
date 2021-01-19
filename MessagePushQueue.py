import logging
from Singleton import Singleton

class MessagePushQueue(Singleton):
    def __init__(self):
        self.pushQueue = []

    def AddMessage(self, version):
        self.pushQueue.append(version)
        logging.debug(f"Add new item: {version}, Queue size: {len(self.pushQueue)}")
    def PopMessage(self):
        try:
            item = self.pushQueue.pop(0)
            logging.debug(f"Pop item: {item}, Queue size: {len(self.pushQueue)}")
        except IndexError:
            # logging.debug(f"Queue is empty.")
            return None

        return item
