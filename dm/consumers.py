from channels.consumer import SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync

from .models import User

import json
import time

class Notifications(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.scope["user"].ws_channel = self.channel_name
        self.scope["user"].save()

    def disconnect(self, close_code):
        self.scope["user"].ws_channel = ''

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']
        message = text_data_json['message']

        print(action, message)

        # Inside a consumer
        async_to_sync(self.channel_layer.send)(
            "long_task",
            {
                "type": "test.print",
                "user_id": self.scope["user"].id,
            },
        )

    def forward(self, event):
        print('forward')
        self.send(json.dumps(event['text']))

    
class Long_Task(SyncConsumer):
    def test_print(self, event):
        print(event)
        time.sleep(10)
        user = User.objects.get(id=event['user_id'])
        async_to_sync(self.channel_layer.send)(user.ws_channel, {'type': 'forward', 'text': 'wow!'})
