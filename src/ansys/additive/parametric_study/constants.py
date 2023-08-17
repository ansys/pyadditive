class ColumnNames:
    """Column names for the parametric study data frame.

    Values are stored internally as a :class:`Pandas DataFrame <pandas.DataFrame>`.
    The column names are defined here.
    """

    #: Name of the parametric summary project.
    PROJECT = "project"
    #: Iteration number, useful for tracking the sequence of simulation groups.
    ITERATION = "iteration"
    #: Priority value used to determine execution order.
    PRIORITY = "priority"
    #: Type of simulation, e.g. single bead, porosity, microstructure.
    TYPE = "type"
    #: Identifier for the simulation.
    #: NOTE: A unique ID for each permutation is enforced by the parametric study.
    ID = "id"
    #: Status of the simulation, e.g. pending, success, failure.
    STATUS = "status"
    #: Name of material used during simulation.
    #: See :class:`AdditiveMaterial <ansys.additive.material.AdditiveMaterial>` for more information.
    MATERIAL = "material"
    #: Heater temperature (°C).
    HEATER_TEMPERATURE = "heater_temperature"
    #: Powder deposition layer thickness (m).
    LAYER_THICKNESS = "layer_thickness"
    #: Laser beam diameter (m).
    BEAM_DIAMETER = "beam_diameter"
    #: Laser power (W).
    LASER_POWER = "laser_power"
    #: Laser scan speed (m/s).
    SCAN_SPEED = "scan_speed"
    #: Hatch scan angle for first layer (°).
    START_ANGLE = "start_angle"
    #: Hatch rotation angle for subsequent layers (°).
    ROTATION_ANGLE = "rotation_angle"
    #: Hatch spacing (m).
    HATCH_SPACING = "hatch_spacing"
    #: Stripe width (m).
    STRIPE_WIDTH = "stripe_width"
    #: Energy density calculated as laser power divided by build rate (J/m^2 or J/m^3).
    ENERGY_DENSITY = "energy_density"
    #: Build rate, calculated as layer thickness * scan speed (m^2/s) for single bead simulations,
    #: or as layer thickness * scan speed * hatch spacing (m^3/s) for porosity and microstructure.
    BUILD_RATE = "build_rate"
    #: Length of single bead to simulate (m).
    SINGLE_BEAD_LENGTH = "single_bead_length"
    #: Median melt pool width measured at the top of the powder layer (m).
    MELT_POOL_WIDTH = "melt_pool_width"
    #: Median melt pool depth measured from the top of the powder layer (m).
    MELT_POOL_DEPTH = "melt_pool_depth"
    #: Median melt pool length measured at the top of the powder layer (m).
    MELT_POOL_LENGTH = "melt_pool_length"
    #: Ratio of MELT_POOL_LENGTH to the median melt pool width at the top of the powder layer.
    MELT_POOL_LENGTH_OVER_WIDTH = "melt_pool_length_over_width"
    #: Median melt pool width measured at the top of the base plate (m).
    MELT_POOL_REFERENCE_WIDTH = "melt_pool_ref_width"
    #: Median melt pool depth measured from the top of the base plate (m).
    MELT_POOL_REFERENCE_DEPTH = "melt_pool_ref_depth"
    #: Ratio of MELT_POOL_REFERENCE_DEPTH to MELT_POOL_REFERENCE_WIDTH.
    MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH = "melt_pool_ref_depth_over_width"
    #: X dimension size of porosity sample to simulate (m).
    POROSITY_SIZE_X = "porosity_size_x"
    #: Y dimension size of porosity sample to simulate (m).
    POROSITY_SIZE_Y = "porosity_size_y"
    #: Z dimension size of porosity sample to simulate (m).
    POROSITY_SIZE_Z = "porosity_size_z"
    #: Relative density of simulated porosity sample.
    RELATIVE_DENSITY = "relative_density"
    #: Minimum X dimension position of microstructure sample (m).
    MICRO_MIN_X = "micro_min_x"
    #: Minimum Y dimension position of microstructure sample (m).
    MICRO_MIN_Y = "micro_min_y"
    #: Minimum Z dimension position of microstructure sample (m).
    MICRO_MIN_Z = "micro_min_z"
    #: X dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_X = "micro_size_x"
    #: Y dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_Y = "micro_size_y"
    #: Z dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_Z = "micro_size_z"
    #: Sensor dimension used in microstructure simulations (m).
    MICRO_SENSOR_DIM = "micro_sensor_dim"
    #: User provided cooling rate used in microstructure simulations (°K/s).
    COOLING_RATE = "cooling_rate"
    #: User provided thermal gradient used in microstructure simulations (°K/m).
    THERMAL_GRADIENT = "thermal_gradient"
    #: User provided melt pool width used in microstructure simulation (m).
    MICRO_MELT_POOL_WIDTH = "micro_melt_pool_width"
    #: User provided melt pool depth used in microstructure simulation (m).
    MICRO_MELT_POOL_DEPTH = "micro_melt_pool_depth"
    #: User provided random seed used in microstructure simulation.
    RANDOM_SEED = "random_seed"
    #: Average microstructure grain size in the XY plane (microns).
    XY_AVERAGE_GRAIN_SIZE = "xy_average_grain_size"
    #: Average microstructure grain size in the XZ plane (microns).
    XZ_AVERAGE_GRAIN_SIZE = "xz_average_grain_size"
    #: Average microstructure grain size in the YY plane (microns).
    YZ_AVERAGE_GRAIN_SIZE = "yz_average_grain_size"
    #: Error message if simulation failed.
    ERROR_MESSAGE = "error_message"


DEFAULT_ITERATION = 0
DEFAULT_PRIORITY = 1
