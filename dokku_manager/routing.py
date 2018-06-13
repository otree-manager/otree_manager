from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.auth import AuthMiddlewareStack

import dm.routing

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            dm.routing.websocket_urlpatterns
        )
    ),
    'channel': ChannelNameRouter({
        "long_task": dm.consumers.Long_Task,
    }),
})