class FakeTensor:
    def __init__(self, value):
        self._value = value

    def item(self):
        return self._value

    def tolist(self):
        return self._value


class FakeBox:
    def __init__(self, conf, xyxy, cls=0):
        self.conf = [FakeTensor(conf)]
        self.xyxy = [FakeTensor(list(xyxy))]
        self.cls = [FakeTensor(cls)]


class FakeResult:
    def __init__(self, boxes, masks=None):
        self.boxes = boxes
        self.masks = masks
