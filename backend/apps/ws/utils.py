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


def notify_alert_ws(user_id: int, unread_count: int):
    """
    Push a real-time alert notification to all browser tabs open for this user.
    Called from the check_price_drops Celery task after new alerts are created.
    """
    channel_layer = get_channel_layer()
    group_name = f"alerts_user_{user_id}"
    message = {
        "type": "alert_message",
        "data": {"type": "new_alerts", "unread_count": unread_count},
    }
    try:
        async_to_sync(channel_layer.group_send)(group_name, message)
    except Exception:
        logger.exception("Failed to send alert WebSocket notification for user %s", user_id)
