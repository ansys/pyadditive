import pytest

from ansys.additive.single_bead import (
    BeadType,
    MeltPool,
    MeltPoolMessage,
    SingleBeadInput,
    SingleBeadSummary,
)

from . import test_utils


def test_MeltPool_init_converts_MeltPoolMessage():
    # arrange, act
    melt_pool = MeltPool(test_utils.get_test_melt_pool_message())

    # assert
    assert len(melt_pool.laser_x) == 1
    assert len(melt_pool.laser_y) == 1
    assert len(melt_pool.length) == 1
    assert len(melt_pool.width) == 1
    assert len(melt_pool.reference_width) == 1
    assert len(melt_pool.depth) == 1
    assert len(melt_pool.reference_depth) == 1
    assert melt_pool.laser_x[0] == 1
    assert melt_pool.laser_y[0] == 2
    assert melt_pool.length[0] == 3
    assert melt_pool.width[0] == 4
    assert melt_pool.reference_width[0] == 5
    assert melt_pool.depth[0] == 6
    assert melt_pool.reference_depth[0] == 7


def test_SingleBeadSummary_init_returns_valid_result():
    # arrange
    melt_pool_msg = test_utils.get_test_melt_pool_message()
    expected_melt_pool = MeltPool(melt_pool_msg)
    machine = test_utils.get_test_machine()
    material = test_utils.get_test_material()
    input = SingleBeadInput(
        id="id",
        bead_type=BeadType.BEAD_ON_BASE_PLATE,
        bead_length=9,
        machine=machine,
        material=material,
    )

    # act
    summary = SingleBeadSummary(input, melt_pool_msg)

    # assert
    assert input == summary.input
    assert expected_melt_pool == summary.melt_pool


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        SingleBeadInput(),
    ],
)
def test_SingleBeadSummary_init_raises_exception_for_invalid_melt_pool_message(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid message type") as exc_info:
        SingleBeadSummary(SingleBeadInput(), invalid_obj)


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        MeltPoolMessage(),
    ],
)
def test_SingleBeadSummary_init_raises_exception_for_invalid_melt_pool_message(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid input type") as exc_info:
        SingleBeadSummary(invalid_obj, MeltPoolMessage())
