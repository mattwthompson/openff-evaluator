"""
A collection of protocols for analyzing the results of binding calculations.
"""

import numpy as np

from propertyestimator import unit
from propertyestimator.protocols.miscellaneous import AddValues
from propertyestimator.thermodynamics import ThermodynamicState
from propertyestimator.utils.quantities import EstimatedQuantity
from propertyestimator.workflow.decorators import protocol_input, protocol_output
from propertyestimator.workflow.plugins import register_calculation_protocol


@register_calculation_protocol()
class AddBindingFreeEnergies(AddValues):
    """A protocol to add together a list of binding free energies.

    Notes
    -----
    The `values` input must either be a list of EstimatedQuantity, a ProtocolPath to a list
    of EstimatedQuantity, or a list of ProtocolPath which each point to a EstimatedQuantity.
    """

    @protocol_input(list)
    def values(self):
        """The values to add together."""
        pass

    @protocol_input(ThermodynamicState)
    def thermodynamic_state(self):
        """The thermodynamic state at which the free energies were measured."""
        pass

    @protocol_input(int)
    def bootstrap_cycles(self):
        """The number of bootstrap cycles to perform when estimating
        the uncertainty in the combined free energies."""
        pass

    @protocol_output(EstimatedQuantity)
    def result(self):
        """The sum of the values."""
        pass

    @protocol_output(unit.Quantity)
    def confidence_intervals(self):
        """The confidence intervals on the summed free energy."""
        pass

    def __init__(self, protocol_id):
        """Constructs a new AddBindingFreeEnergies object."""
        super().__init__(protocol_id)

        self._values = None
        self._thermodynamic_state = None
        self._bootstrap_cycles = 1000

        self._result = None
        self._confidence_intervals = None

    def execute(self, directory, available_resources):

        mean, uncertainty, confidence_intervals = self.bootstrap()

        self._result = EstimatedQuantity(mean,
                                         uncertainty,
                                         self._id)

        self._confidence_intervals = confidence_intervals

        return self._get_output_dictionary()

    def bootstrap(self):
        """

        Returns
        -------
        unit.Quantity
            The summed free energies.
        unit.Quantity
            The uncertainty in the summed free energies
        unit.Quantity
            A unit wrapped list of the confidence intervals.
        """

        default_unit = unit.kilocalorie / unit.mole

        boltzmann_factor = self.thermodynamic_state.temperature * unit.molar_gas_constant
        boltzmann_factor.ito(default_unit)

        beta = 1.0 / boltzmann_factor

        cycle_result = np.empty(self.bootstrap_cycles)

        for cycle_index, cycle in enumerate(range(self.bootstrap_cycles)):

            cycle_values = np.empty(len(self._values))

            for value_index, value in enumerate(self._values):
                mean = value.value.to(default_unit).magnitude
                sem = value.uncertainty.to(default_unit).magnitude

                sampled_value = np.random.normal(mean, sem) * default_unit
                cycle_values[value_index] = (-beta * sampled_value).to(unit.dimensionless).magnitude

            # ΔG° = -RT × Log[ Σ_{n} exp(-βΔG°_{n}) ]

            cycle_result[cycle_index] = np.log(np.sum(np.exp(cycle_values)))

        mean = np.mean(-boltzmann_factor * cycle_result)
        sem = np.std(-boltzmann_factor * cycle_result)

        confidence_intervals = np.empty(2)
        sorted_statistics = np.sort(cycle_result)
        confidence_intervals[0] = sorted_statistics[int(0.025 * self.bootstrap_cycles)]
        confidence_intervals[1] = sorted_statistics[int(0.975 * self.bootstrap_cycles)]

        confidence_intervals = -boltzmann_factor * confidence_intervals

        return mean, sem, confidence_intervals


@register_calculation_protocol()
class AddBindingEnthalpies(AddValues):
    """A protocol to add together a list of binding free enthalpies.

    Notes
    -----
    The `values` input must either be a list of EstimatedQuantity, a ProtocolPath to a list
    of EstimatedQuantity, or a list of ProtocolPath which each point to a EstimatedQuantity.

    With multiple binding orientations, the binding enthalpy of each orientation is weighted its respective
    binding free energy, and therefore this class must accept both binding enthalpies and binding free energies.

    For more information, see:
    Computational Calorimetry: High-Precision Calculation of Host–Guest Binding Thermodynamics
    Niel M. Henriksen, Andrew T. Fenley, Michael K. Gilson
    Journal of Chemical Theory and Computation (2015-08-26) https://doi.org/f7q3mj
    DOI: 10.1021/acs.jctc.5b00405 · PMID: 26523125 · PMCID: PMC4614838
    """

    @protocol_input(list)
    def enthalpy_free_energy_tuple(self):
        """The enthalpies to add together, passed as a tuple with their respective binding free energies."""
        pass

    @protocol_input(ThermodynamicState)
    def thermodynamic_state(self):
        """The thermodynamic state at which the free energies were measured."""
        pass

    @protocol_input(int)
    def bootstrap_cycles(self):
        """The number of bootstrap cycles to perform when estimating
        the uncertainty in the combined free energies."""
        pass

    @protocol_output(EstimatedQuantity)
    def result(self):
        """The sum of the values."""
        pass

    @protocol_output(unit.Quantity)
    def confidence_intervals(self):
        """The confidence intervals on the summed enthalpy."""
        pass

    def __init__(self, protocol_id):
        """Constructs a new AddBindingEnthalpies object."""
        super().__init__(protocol_id)

        self._values = None
        self._thermodynamic_state = None
        self._bootstrap_cycles = 1000

        self._result = None
        self._confidence_intervals = None

    def execute(self, directory, available_resources):

        mean, uncertainty, confidence_intervals = self.bootstrap()

        self._result = EstimatedQuantity(mean,
                                         uncertainty,
                                         self._id)

        return self._get_output_dictionary()

    def bootstrap(self):
        """

        Returns
        -------
        unit.Quantity
            The summed enthalpies.
        unit.Quantity
            The uncertainty in the summed enthalpies
        unit.Quantity
            A unit wrapped list of the confidence intervals.
        """

        default_unit = unit.kilocalorie / unit.mole

        boltzmann_factor = self.thermodynamic_state.temperature * unit.molar_gas_constant
        boltzmann_factor.ito(default_unit)

        beta = 1.0 / boltzmann_factor

        cycle_result = np.empty(self._bootstrap_cycles)

        for cycle_index, cycle in enumerate(range(self._bootstrap_cycles)):

            cycle_values = np.empty((len(self._values), 2))

            for value_index, value in enumerate(self._values):
                mean_enthalpy = value[0].value.to(default_unit).magnitude
                sem_enthalpy = value[0].uncertainty.to(default_unit).magnitude

                mean_free_energy = value[1].value.to(default_unit).magnitude
                sem_free_energy = value[1].uncertainty.to(default_unit).magnitude

                sampled_enthalpy = np.random.normal(mean_enthalpy, sem_enthalpy) * default_unit
                sampled_free_energy = np.random.normal(mean_free_energy, sem_free_energy) * default_unit

                cycle_values[value_index][0] = sampled_enthalpy.to(default_unit).magnitude
                cycle_values[value_index][1] = (-beta * sampled_free_energy).to(unit.dimensionless).magnitude

            #      Σ_{n} [ ΔH_{n} × exp(-βΔG°_{n}) ]
            # ΔH = ---------------------------------
            #            Σ_{n} exp(-βΔG°_{n})

            cycle_result[cycle_index] = np.sum(cycle_values[:, 0] * np.exp(cycle_values[:, 1])) \
                                        / np.sum(np.exp(cycle_values[:, 1]))

        mean = np.mean(cycle_result) * default_unit
        sem = np.std(cycle_result) * default_unit

        confidence_intervals = np.empty(2)
        sorted_statistics = np.sort(cycle_result)
        confidence_intervals[0] = sorted_statistics[int(0.025 * self._bootstrap_cycles)]
        confidence_intervals[1] = sorted_statistics[int(0.975 * self._bootstrap_cycles)]

        return mean, sem, confidence_intervals * default_unit