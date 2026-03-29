CHANNELS = ["BBC", "Discovery", "TV1000"]

class TVController:
    def __init__(self, channels):
        self.channels = channels
        self.current = 0

    def first_channel(self):
        self.current = 0
        return self.channels[self.current]

    def last_channel(self):
        self.current = -1
        return self.channels[self.current]

    def turn_channel(self, N):
        self.current = N - 1
        try:
            return self.channels[self.current]
        except IndexError:
            print(f'Каналу {N} немає')

    def next_channel(self):
        if self.current + 1 < len(self.channels):
            self.current += 1

        else:
            self.current = 0
        return self.channels[self.current]

    def previous_channel(self):
        if self.current > 0:
            self.current -= 1

        else:
            self.current = -1
        return self.channels[self.current]

    def current_channel(self):
        return self.channels[self.current]

    def exists(self, arg):
        if isinstance(arg, int):
            if 1 <= arg <= len(self.channels):
                return 'Yes'
            else:
                return 'No'

        elif isinstance(arg, str):
            if arg in self.channels:
                return 'Yes'
            else:
                return 'No'

        else:
            return 'No'



controller = TVController(CHANNELS)

print(
controller.first_channel() == "BBC" ,
controller.last_channel() == "TV1000" ,
controller.turn_channel(1) == "BBC" ,
controller.next_channel() == "Discovery" ,
controller.previous_channel() == "BBC" ,
controller.current_channel() == "BBC" ,
controller.exists(4) == "No" ,
controller.exists("BBC") == "Yes"
)