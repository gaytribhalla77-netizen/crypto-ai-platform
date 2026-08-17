import json
class AuditLogger:
    def event(self, event_type, user_id, data):
        return {
            "event_type": event_type,
            "user_id": user_id,
            "data": json.dumps(data, default=str)
        }
