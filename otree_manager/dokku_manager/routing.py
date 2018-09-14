from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.auth import AuthMiddlewareStack

import dokku_manager.om.routing

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            dokku_manager.om.routing.websocket_urlpatterns
        )
    ),
    'channel': ChannelNameRouter({
        "dokku_tasks": dokku_manager.om.consumers.Dokku_Tasks,
    }),
})
