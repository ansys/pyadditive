# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import random
import socket
import string


def check_valid_ip(ip):
    """Check for valid IP address."""
    if ip.lower() != "localhost":
        ip = ip.replace('"', "").replace("'", "")
        socket.inet_aton(ip)


def check_valid_port(port, lower_bound=1000, high_bound=60000):
    """Check for valid port number."""
    _port = int(port)

    if lower_bound < _port < high_bound:
        return
    else:
        raise ValueError(f"'port' values should be between {lower_bound} and {high_bound}.")


def short_uuid() -> str:
    """Generate a short UUID."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=8))
