from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from .utils import build_routepatterns


routeprefixes = {
}

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            build_routepatterns(routeprefixes)
        )
    ),
})
