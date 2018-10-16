from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.auth import AuthMiddlewareStack

import otree_manager.om.routing

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            otree_manager.om.routing.websocket_urlpatterns
        )
    ),
    'channel': ChannelNameRouter({
        "otree_manager_tasks": otree_manager.om.consumers.OTree_Manager_Tasks,
    }),
})
