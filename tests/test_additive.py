# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from unittest.mock import create_autospec

import ansys.platform.instancemanagement as pypim
import grpc
import pytest

from ansys.additive import (
    MAX_MESSAGE_LENGTH,
    Additive,
    MicrostructureInput,
    PorosityInput,
    SingleBeadInput,
    ThermalHistoryInput,
)
import ansys.additive.additive


def test_Additive_init_connects_with_defaults(monkeypatch):
    # arrange
    target = "127.0.0.1:50052"
    channel = grpc.insecure_channel(
        "channel_str",
        options=[
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    )

    mock_launcher = create_autospec(ansys.additive.additive.launch_server, return_value=None)
    monkeypatch.setattr(ansys.additive.additive, "launch_server", mock_launcher)
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=channel)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)

    # act
    additive = Additive()

    # assert
    mock_insecure_channel.assert_called_with(
        target, options=[("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH)]
    )
    assert additive._channel == channel
    assert hasattr(additive, "_server_instance") == False


def test_Additive_init_can_connect_with_pypim(monkeypatch):
    # assemble
    mock_instance = pypim.Instance(
        definition_name="definition",
        name="name",
        ready=True,
        status_message=None,
        services={"grpc": pypim.Service(uri="dns:ip:port", headers={})},
    )
    pim_channel = grpc.insecure_channel(
        "channel_str",
        options=[
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    )
    mock_instance.wait_for_ready = create_autospec(mock_instance.wait_for_ready)
    mock_instance.delete = create_autospec(mock_instance.delete)

    mock_client = pypim.Client(channel=grpc.insecure_channel("localhost:12345"))
    mock_client.create_instance = create_autospec(
        mock_client.create_instance, return_value=mock_instance
    )

    mock_connect = create_autospec(pypim.connect, return_value=mock_client)
    mock_is_configured = create_autospec(pypim.is_configured, return_value=True)
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=pim_channel)
    monkeypatch.setattr(pypim, "connect", mock_connect)
    monkeypatch.setattr(pypim, "is_configured", mock_is_configured)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)

    # act
    additive = Additive()

    # assert
    assert mock_is_configured.called
    assert mock_connect.called
    mock_client.create_instance.assert_called_with(product_name="additive", product_version=None)
    assert mock_instance.wait_for_ready.called
    assert additive._channel == pim_channel
    assert additive._server_instance == mock_instance
    mock_insecure_channel.assert_called_with(
        "ip:port", options=[("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH)]
    )

    # verify that destructor deletes the instance
    additive.__del__()
    assert mock_instance.delete.called


def test_Additive_init_connects_using_ANSYS_ADDITIVE_ADDRESS_if_available(monkeypatch):
    # arrange
    target = "localhost:12345"
    monkeypatch.setenv("ANSYS_ADDITIVE_ADDRESS", target)
    channel = grpc.insecure_channel(
        "channel_str",
        options=[
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    )
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=channel)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)

    # act
    additive = Additive()

    # assert
    mock_insecure_channel.assert_called_with(
        target, options=[("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH)]
    )
    assert additive._channel == channel
    assert hasattr(additive, "_server_instance") == False


def test_Additive_init_connects_with_ip_and_port_parameters(monkeypatch):
    # arrange
    ip = "1.2.3.4"
    port = 12345
    target = f"{ip}:{port}"
    channel = grpc.insecure_channel(
        "channel_str",
        options=[
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    )
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=channel)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)

    # act
    additive = Additive(ip=ip, port=port)

    # assert
    mock_insecure_channel.assert_called_with(
        target, options=[("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH)]
    )
    assert additive._channel == channel
    assert hasattr(additive, "_server_instance") == False


@pytest.mark.parametrize(
    "input",
    [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        ThermalHistoryInput(),
    ],
)
def test_simulate_without_material_assigned_raises_exception(input):
    # arrange
    additive = Additive(ip="localhost", port=12345)

    # act, assert
    with pytest.raises(ValueError, match="Material must be specified"):
        additive.simulate(input)


def test_simulate_list_of_inputs_with_duplicate_ids_raises_exception():
    # arrange
    additive = Additive(ip="localhost", port=12345)
    inputs = [
        SingleBeadInput(id="id"),
        SingleBeadInput(id="id"),
    ]

    # act, assert
    with pytest.raises(ValueError, match='Duplicate simulation id "id" in input list'):
        additive.simulate(inputs)
