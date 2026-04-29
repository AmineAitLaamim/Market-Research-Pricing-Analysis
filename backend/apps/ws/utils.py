import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def _do_notify_ws(search_id, event_type, payload):
    """Send a progress message to the WebSocket group for this search."""
    channel_layer = get_channel_layer()
    group_name = f"search_{search_id}"
    message = {
        "type": "progress_message",
        "data": {"type": event_type, **payload},
    }
    try:
        async_to_sync(channel_layer.group_send)(group_name, message)
    except Exception:
        logger.exception("Failed to send WebSocket notification for search %s", search_id)

import threading
def notify_ws(search_id, event_type, payload):
    t = threading.Thread(target=_do_notify_ws, args=(search_id, event_type, payload))
    t.start()
    t.join()
