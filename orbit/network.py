"""Trusted IPv4 interfaces offered for phone pairing."""

import ipaddress
import socket

LAN_NETWORKS = tuple(
    ipaddress.IPv4Network(cidr) for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


def lan_addresses() -> list[str]:
    addresses = set()
    preferred = None
    try:
        # UDP connect selects the default route. It does not send a packet.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("1.1.1.1", 53))
            preferred = probe.getsockname()[0]
            addresses.add(preferred)
    except OSError:
        pass
    try:
        addresses.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    return sorted(
        (value for value in addresses if any(ipaddress.IPv4Address(value) in net for net in LAN_NETWORKS)),
        key=lambda value: (value != preferred, ipaddress.IPv4Address(value)),
    )
