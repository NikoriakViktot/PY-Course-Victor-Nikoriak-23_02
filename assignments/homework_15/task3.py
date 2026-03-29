class TVController:
    def __init__(self, channels):
        self.channels = channels
        self.index = 0

    def current_channel(self):
        return self.channels[self.index]

    def first_channel(self):
        self.index = 0
        return self.current_channel()

    def last_channel(self):
        self.index = len(self.channels) - 1
        return self.current_channel()

    def next_channel(self):
        self.index += 1
        if self.index >= len(self.channels):
            self.index = 0
        return self.current_channel()

    def previous_channel(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.channels) - 1
        return self.current_channel()

    def turn_channel(self, n):
        self.index = n - 1
        return self.current_channel()

    def exists(self, arg):
        if isinstance(arg, int):
            if 1 <= arg <= len(self.channels):
                return 'Yes'
        elif isinstance(arg, str):
            if arg in self.channels:
                return 'Yes'

        return 'No'

CHANNELS = ["BBC", "Discovery", "TV1000"]
controller = TVController(CHANNELS)

# Перевірки (мають повернути True)
print(controller.first_channel() == "BBC")
print(controller.last_channel() == "TV1000")
print(controller.turn_channel(1) == "BBC")
print(controller.next_channel() == "Discovery")
print(controller.previous_channel() == "BBC")
print(controller.current_channel() == "BBC")
print(controller.exists(4) == "No")
print(controller.exists("BBC") == "Yes")



