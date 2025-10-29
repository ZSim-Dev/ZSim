


class EventRouter:
    def __init__(self):
        self.handler_map = {}
        self.event_trigger_tree = None
        self.active_event_list = []

