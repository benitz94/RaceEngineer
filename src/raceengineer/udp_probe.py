"""UDP transport diagnostics only; no payload parsing or retention."""

from dataclasses import asdict, dataclass
import socket
import time


@dataclass(frozen=True)
class DatagramInfo:
    peer: tuple[str, int]
    size: int
    recv_ts: float

    def to_dict(self):
        return asdict(self)


def receive_info(sock):
    payload, peer = sock.recvfrom(65535)
    return DatagramInfo(peer, len(payload), time.time())


def probe(port, host="0.0.0.0", count=None):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        received = 0
        while count is None or received < count:
            yield receive_info(sock)
            received += 1
