# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from ansys.additive.core import SimulationError, SingleBeadInput


def test_SimulationError_init_assigns_values():
    # arrange
    input = SingleBeadInput(id="id")

    # act
    error = SimulationError(input=input, message="message")

    # assert
    assert error.input == input
    assert error.message == "message"
