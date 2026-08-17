class NotificationService:
    PRIORITY = {"LOW":1,"MEDIUM":2,"HIGH":3,"CRITICAL":4}

    def should_send(self, priority, last_priority=None):
        if priority not in self.PRIORITY:
            return False
        return last_priority is None or self.PRIORITY[priority] >= self.PRIORITY.get(last_priority,0)

    async def event(self, event_type, priority, payload):
        return {"event":event_type,"priority":priority,"payload":payload}
