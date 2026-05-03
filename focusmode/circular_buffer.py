class CircularBuffer:
    def __init__(self, size=100):
        self.size   = size
        self.buffer = [None] * size
        self.head   = 0
        self.count  = 0

    def add(self, item):
        self.buffer[self.head] = item
        self.head = (self.head + 1) % self.size
        if self.count < self.size:
            self.count += 1

    def get_all(self):
        return [item for item in self.buffer if item is not None]

    def focus_percentage(self):
        all_items = self.get_all()
        if len(all_items) == 0:
            return 0.0
        focused_count = sum(1 for item in all_items if item == "FOCUSED")
        return (focused_count / len(all_items)) * 100

    def drowsy_count(self):
        return sum(1 for item in self.get_all() if item == "DROWSY")

    def distracted_count(self):
        return sum(1 for item in self.get_all() if item == "DISTRACTED")