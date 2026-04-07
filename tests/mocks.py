import time


class MockSendResult:
    """Mimics the result object returned by meshcore send_msg."""
    def __init__(self, msg_type='MSG_SENT'):
        self.type = msg_type
        self.payload = {'type': 1, 'expected_ack': b'\x00\x00\x00\x00', 'suggested_timeout': 500}


class MockCommands:
    def __init__(self):
        self.sent = []

    async def send_msg(self, dst=None, msg=None, **kwargs):
        # simulate network send delay
        self.sent.append((dst, msg))
        return MockSendResult()


class MockMesh:
    def __init__(self):
        self.commands = MockCommands()
        self.subscriptions = {}

    @classmethod
    async def create_serial(cls, device=None, baud=None):
        return cls()

    @classmethod
    async def create_tcp(cls, host=None, port=None):
        return cls()

    def subscribe(self, event, callback):
        self.subscriptions.setdefault(event, []).append(callback)

    async def close(self):
        return True


class MockSender:
    def __init__(self, fobj, packets=None):
        self.fobj = fobj
        # default to single small packet
        self.packets = packets if packets is not None else [b"MOCKDATA"]
        self._idx = 0
        self.state = 'init'
        self.offset = 0

    def is_finished(self):
        return self._idx >= len(self.packets)

    def get_next_packet(self):
        if self._idx < len(self.packets):
            p = self.packets[self._idx]
            self._idx += 1
            self.state = 'sending'
            return p
        self.state = 'finished'
        return b""


class MockReceiver:
    def __init__(self, fobj_or_path):
        if isinstance(fobj_or_path, str):
            self.filepath = fobj_or_path
            self.fobj = None
        else:
            self.filepath = None
            self.fobj = fobj_or_path
        self._finished = False
        self.filename = None
        self.expected_size = 0
        self.state = 'waiting'

    def receive(self, data):
        # open file on first write when given a path (matches real Receiver)
        if data:
            if self.fobj is None and self.filepath:
                self.fobj = open(self.filepath, 'wb')
            if self.fobj:
                self.fobj.write(data)
        self._finished = True

    def is_finished(self):
        return self._finished
