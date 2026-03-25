# MuJoCo Motors Assets

This repository serves as the official motor database for the **mjlab** project. Our goal is to provide a comprehensive, standardized, and easily accessible collection of motor specifications and simulation data for robotics applications, particularly for those using **MuJoCo**.

This database is a key part of the mjlab simulation environment, built according to the **[motor database design proposal](https://github.com/robomotic/mjlab/blob/feature/motor-database-extension/docs/motors/design-proposal.md)**.

## Repository Structure

The core of the repository is located in the `motor_assets/` directory.

### `motor_assets/`
Each subdirectory corresponds to a motor vendor:

- **Vendor Folder**: (e.g., `maxon/`, `faulhaber/`, `t_motor/`, `unitree/`, etc.)
    - `info.md`: Contains a link to the vendor's official website.
    - `[motor_model].json`: Technical parameters including gear ratio, resistance, inductance, torque constants, and sensor details.
    - `[model_id].step`: CAD geometry file.
    - `[model_id].stl`: Mesh file for simulation/visualization.

### `utils/`
Contains Python utilities for working with the motor database, including scripts for data validation, format conversion, and simulation integration.

For detailed instructions on how to properly model a motor, refer to the **[Example Model Motor Wiki](https://github.com/robomotic/mujoco-motors/wiki/Example-Model-Motor)**.

## Motor Metadata Schema

The JSON files for each motor follow a structured schema for compatibility with simulation environments.

Example (`maxon/maxon_ec_i_40_488607.json`):

```json
{
{
    "motor_id": "maxon_ec_i_40_488607",
    "manufacturer": "Maxon",
    "model": "EC-i 40 (488607)",
    "step_file": "https://github.com/robomotic/mujoco-motors/blob/main/motor_assets/maxon/488607.step",
    "stl_file": "https://github.com/robomotic/mujoco-motors/blob/main/motor_assets/maxon/488607.stl",
    "gear_ratio": 1.0,
    "reflected_inertia": 4.4e-06,
    "voltage_range": [
        0.0,
        48.0
    ],
    "resistance": 0.994,
    "inductance": 0.000995,
    "motor_constant_kt": 0.091,
    "motor_constant_ke": 0.091,
    "stall_torque": 2.08,
    "continuous_torque": 0.224,
    "no_load_speed": 523.6,
    "no_load_current": 0.15,
    "thermal_resistance": 8.52,
    "max_winding_temperature": 155.0,
    "stall_current": 48.2897,
    "peak_torque": 2.08,
    "rotation_angle_range": [
        0,
        0
    ],
    "thermal_time_constant": null,
    "ambient_temperature": 25.0,
    "encoder_resolution": 0,
    "encoder_type": "unknown",
    "feedback_sensors": [],
    "protocol": "unknown",
    "protocol_params": {},
    "operating_current": null
}
}
```

## Tooling & Workflow

To maintain the quality and completeness of the motor database, the `utils/` directory contains tools to assist in creating and verifying assets.

### 1. `extrapolator.py`
Many vendor datasheets are missing critical fields. This script uses standard electromechanical formulas to derive missing parameters (such as Back-EMF constants, stall current, or peak torque) from the values you provide. It also fills in safe default values for categorical fields like protocols and sensor types.

**When to use:** Run this immediately after creating a new JSON file with initial data from a datasheet.

```bash
# Run on a single file (always recommended to try --dry-run first)
python3 utils/extrapolator.py --input motor_assets/maxon/488607.json

# Run on all assets in the repository
python3 utils/extrapolator.py --all
```

### 2. `validate_motors.py`
Ensures that all JSON files match the required `MotorSpecification` schema, verifies data types, and flags missing values.

**When to use:** Run this to confirm your contribution is complete before submitting.

```bash
python3 utils/validate_motors.py --root motor_assets
```

---

## Contributing

To add a new vendor or motor asset, please **create an issue** in the repository first.

### Recommended Contribution Workflow:
1. **Create** the motor folder and initial `.json` file with vendor values.
2. **Run [extrapolator.py](utils/extrapolator.py)** to fill in derived constants and defaults.
3. **Manually check** any fields marked as `None` or `WARNING` (some fields like `thermal_time_constant` cannot be calculated and must be provided manually).
4. **Run [validate_motors.py](utils/validate_motors.py)**; the final asset is only ready once it passes validation with no errors.
5. Create a Pull Request with the updated JSON and associated 3D models.
