"""
Units tests for propertyestimator.protocols.miscellaneous
"""
import pytest

from propertyestimator import unit
from propertyestimator.backends import ComputeResources
from propertyestimator.protocols.miscellaneous import AddBindingFreeEnergies, AddBindingEnthalpies
from propertyestimator.thermodynamics import ThermodynamicState
from propertyestimator.utils.quantities import EstimatedQuantity


def test_add_binding_free_energies_protocol():
    """Tests adding together two binding free energies. """

    compute_resources = ComputeResources(number_of_threads=1)

    delta_g_one = EstimatedQuantity(-10.0 * unit.kilocalorie / unit.mole,
                                    1.0 * unit.kilocalorie / unit.mole, 'test_source_1')

    delta_g_two = EstimatedQuantity(-20.0 * unit.kilocalorie / unit.mole,
                                    2.0 * unit.kilocalorie / unit.mole, 'test_source_2')

    thermodynamic_state = ThermodynamicState(298 * unit.kelvin, 1 * unit.atmosphere)

    sum_protocol = AddBindingFreeEnergies("add_binding_free_energies")

    sum_protocol.values = [delta_g_one, delta_g_two]
    sum_protocol.thermodynamic_state = thermodynamic_state

    sum_protocol.execute('', compute_resources)

    assert isinstance(sum_protocol.result, EstimatedQuantity)
    assert sum_protocol.result.value.magnitude == pytest.approx(-20.0, abs=0.1)
    assert sum_protocol.result.uncertainty.magnitude == pytest.approx(2.0, abs=0.1)
    assert sum_protocol.result.value.units == unit.kilocalorie / unit.mole


def test_add_binding_free_energy_protocol_unit_handling():
    """Tests adding together two binding free energies with unit conversion. """

    compute_resources = ComputeResources(number_of_threads=1)

    delta_g_one = EstimatedQuantity((-10.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    (1.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    'test_source_1')

    delta_g_two = EstimatedQuantity((-20.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    (2.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    'test_source_2')

    thermodynamic_state = ThermodynamicState(298 * unit.kelvin, 1 * unit.atmosphere)

    sum_protocol = AddBindingFreeEnergies("add_binding_free_energies")

    sum_protocol.values = [delta_g_one, delta_g_two]
    sum_protocol.thermodynamic_state = thermodynamic_state

    sum_protocol.execute('', compute_resources)

    assert isinstance(sum_protocol.result, EstimatedQuantity)
    assert sum_protocol.result.value.magnitude == pytest.approx(-20.0, abs=0.1)
    assert sum_protocol.result.uncertainty.magnitude == pytest.approx(2.0, abs=0.1)
    assert sum_protocol.result.value.units == unit.kilocalorie / unit.mole


def test_add_binding_free_energy_protocol_cycle_convergence():
    """Tests adding together two binding free energies uses sufficient number of bootstrap samples. """

    compute_resources = ComputeResources(number_of_threads=1)

    delta_g_one = EstimatedQuantity((-10.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    (1.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    'test_source_1')

    delta_g_two = EstimatedQuantity((-20.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    (2.0 * unit.kilocalorie / unit.mole).to(unit.kilojoule / unit.mole),
                                    'test_source_2')

    thermodynamic_state = ThermodynamicState(298 * unit.kelvin, 1 * unit.atmosphere)

    sum_protocol = AddBindingFreeEnergies("add_binding_free_energies")

    sum_protocol.values = [delta_g_one, delta_g_two]
    sum_protocol.thermodynamic_state = thermodynamic_state

    for cycle_exponent in range(3, 5):
        sum_protocol.cycles = 10 ** cycle_exponent
        sum_protocol.execute('', compute_resources)

        assert isinstance(sum_protocol.result, EstimatedQuantity)
        assert sum_protocol.result.value.magnitude == pytest.approx(-20.0, abs=0.1)
        assert sum_protocol.result.uncertainty.magnitude == pytest.approx(2.0, abs=0.1)
        assert sum_protocol.result.value.units == unit.kilocalorie / unit.mole


def test_add_binding_enthalpies_protocol():
    """Tests adding together two binding enthalpies with associated binding free energies. """

    compute_resources = ComputeResources(number_of_threads=1)

    delta_g_one = EstimatedQuantity(-10.0 * unit.kilocalorie / unit.mole,
                                    1.0 * unit.kilocalorie / unit.mole, 'test_source_1')

    delta_h_one = EstimatedQuantity(-2.0 * unit.kilocalorie / unit.mole,
                                    1.0 * unit.kilocalorie / unit.mole, 'test_source_1')

    delta_g_two = EstimatedQuantity(-20.0 * unit.kilocalorie / unit.mole,
                                    2.0 * unit.kilocalorie / unit.mole, 'test_source_2')

    delta_h_two = EstimatedQuantity(-4.0 * unit.kilocalorie / unit.mole,
                                    2.0 * unit.kilocalorie / unit.mole, 'test_source_2')

    thermodynamic_state = ThermodynamicState(298 * unit.kelvin, 1 * unit.atmosphere)

    sum_protocol = AddBindingEnthalpies("add_binding_enthalpies")

    sum_protocol.values = [(delta_h_one, delta_g_one,), (delta_h_two, delta_g_two)]
    sum_protocol.thermodynamic_state = thermodynamic_state

    sum_protocol.execute('', compute_resources)

    assert isinstance(sum_protocol.result, EstimatedQuantity)
    assert sum_protocol.result.value.magnitude == pytest.approx(-4.0, abs=0.1)
    assert sum_protocol.result.uncertainty.magnitude == pytest.approx(2.0, abs=0.1)
    assert sum_protocol.result.value.units == unit.kilocalorie / unit.mole