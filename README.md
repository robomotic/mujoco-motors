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

For detailed instructions on how to properly model a motor, refer to the **[Example Model Motor Wiki](https://github.com/robomotic/mujoco-motors/wiki/Example-Model-Motor)**.

## Motor Metadata Schema

The JSON files for each motor follow a structured schema for compatibility with simulation environments.

Example (`maxon/maxon_ec_i_40_488607.json`):

```json
{
  "motor_id": "maxon_ec_i_40_488607",
  "manufacturer": "Maxon",
  "model": "EC-i 40 (488607)",
  "step_file": "https://github.com/robomotic/mujoco-motors/blob/main/motor_assets/maxon/488607.step",
  "stl_file": "https://github.com/robomotic/mujoco-motors/blob/main/motor_assets/maxon/488607.stl",
  "gear_ratio": 1.0,
  "reflected_inertia": 4.4e-06,
  "rotation_angle_range": [0, 0],
  "voltage_range": [0.0, 48.0],
  "resistance": 0.994,
  "inductance": 0.000995,
  "motor_constant_kt": 0.091,
  "motor_constant_ke": 0.091,
  "stall_torque": 2.08,
  "peak_torque": 2.08,
  "continuous_torque": 0.224,
  "no_load_speed": 523.6,
  "no_load_current": 0.150,
  "stall_current": 48.3,
  "operating_current": 2.41,
  "thermal_resistance": 8.52,
  "thermal_time_constant": 1400.0,
  "max_winding_temperature": 155.0,
  "ambient_temperature": 25.0,
  "encoder_resolution": 42,
  "encoder_type": "hall_sensors",
  "feedback_sensors": ["position", "velocity", "hall"],
  "protocol": "PWM",
  "protocol_params": {}
}
```

## Contributing

To add a new vendor or motor asset, please **create an issue** in the repository first. This allows the maintainers to review the request and coordinate the technical details.

When contributing:
1. Create a folder under `motor_assets/` (if it doesn't already exist).
2. Add an `info.md` file with the official website link.
3. Include the `.json` metadata and any relevant `.step` or `.stl` files.
