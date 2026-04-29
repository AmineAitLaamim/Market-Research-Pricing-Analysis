import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SearchConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live search progress updates.

    Clients connect to: /ws/search/<search_id>/
    They receive JSON messages shaped as:
      { "type": "status"|"scraping"|"mining"|"completed"|"error", ... }
    """

    async def connect(self):
        self.search_id = self.scope["url_route"]["kwargs"]["search_id"]
        self.group_name = f"search_{self.search_id}"

        # Join the group for this search
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WS connected: group=%s", self.group_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.debug("WS disconnected: group=%s code=%s", self.group_name, close_code)

    # Receive a message from the WebSocket client (not used server→client only)
    async def receive(self, text_data=None, bytes_data=None):
        pass

    # Handler called by channel_layer.group_send(type="progress_message")
    async def progress_message(self, event):
        """Forward a progress payload to the connected WebSocket client."""
        await self.send(text_data=json.dumps(event["data"]))
