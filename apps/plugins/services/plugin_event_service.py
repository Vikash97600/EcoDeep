import json
from apps.plugins.models import PluginEvent

class PluginEventService:
    """Event bus broadcasting platform lifecycle events for subscriber plugins."""

    @staticmethod
    def emit_event(event_type: str, payload: dict):
        """Emits an event to the PluginEvent bus ledger."""
        return PluginEvent.objects.create(
            event_type=event_type,
            payload_json=json.dumps(payload)
        )
