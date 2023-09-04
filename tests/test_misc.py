# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import pytest

from ansys.additive.core import misc


def test_valid_ip_returns_without_error_for_valid_values():
    # arrange, act, assert
    misc.check_valid_ip("1.2.3.4")
    misc.check_valid_ip("127.0.0.1")
    misc.check_valid_ip("8.8.8.8")
    misc.check_valid_ip("localhost")


def test_valid_ip_raises_error_for_invalid_values():
    # arrange, act, assert
    with pytest.raises(OSError):
        misc.check_valid_ip("google.com")
    with pytest.raises(OSError):
        misc.check_valid_ip("")


def test_check_valid_port_returns_without_error_for_valid_values():
    # arrange, act, assert
    misc.check_valid_port(1001)
    misc.check_valid_port(59999)
    misc.check_valid_port("1001")
    misc.check_valid_port("1", 0, 2)


def test_check_valid_port_raises_error_for_invalid_values():
    # arrange, act, assert
    with pytest.raises(ValueError):
        misc.check_valid_port(1000)
    with pytest.raises(ValueError):
        misc.check_valid_port(60000)
    with pytest.raises(ValueError):
        misc.check_valid_port("1000")
    with pytest.raises(ValueError):
        misc.check_valid_port("0", 0, 2)


def test_short_uuid_returns_string_of_expected_length():
    # arrange, act
    result = misc.short_uuid()

    # assert
    assert isinstance(result, str)
    assert len(result) == 8
