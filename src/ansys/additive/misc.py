import socket


def check_valid_ip(ip):
    """Check for valid IP address"""
    if ip.lower() != "localhost":
        ip = ip.replace('"', "").replace("'", "")
        socket.inet_aton(ip)


def check_valid_port(port, lower_bound=1000, high_bound=60000):
    _port = int(port)

    if lower_bound < _port < high_bound:
        return
    else:
        raise ValueError(f"'port' values should be between {lower_bound} and {high_bound}.")
