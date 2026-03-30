CHANNELS = ["BBC", "Discovery", "TV1000"]


class TVController:
    def __init__(self, channels):
        self.channels = channels
        self.current_index = 0

    def first_channel(self):
        self.current_index = 0
        return self.channels[self.current_index]

    def last_channel(self):
        self.current_index = len(self.channels) - 1
        return self.channels[self.current_index]

    def turn_channel(self, N):
        self.current_index = N - 1
        return self.channels[self.current_index]

    def next_channel(self):
        self.current_index = (self.current_index + 1) % len(self.channels)
        return self.channels[self.current_index]

    def previous_channel(self):
        self.current_index = (self.current_index - 1) % len(self.channels)
        return self.channels[self.current_index]

    def current_channel(self):
        return self.channels[self.current_index]

    def exists(self, value):
        if isinstance(value, int):
            return "Yes" if 1 <= value <= len(self.channels) else "No"
        elif isinstance(value, str):
            return "Yes" if value in self.channels else "No"
        return "No"


# Test
controller = TVController(CHANNELS)

print(controller.first_channel())     # BBC
print(controller.last_channel())      # TV1000
print(controller.turn_channel(1))     # BBC
print(controller.next_channel())      # Discovery
print(controller.previous_channel())  # BBC
print(controller.current_channel())   # BBC
print(controller.exists(4))           # No
print(controller.exists("BBC"))       # Yes