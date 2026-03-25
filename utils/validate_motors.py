import os
import json
import argparse
from dataclasses import dataclass, fields
from typing import Optional, Any

@dataclass
class MotorSpecification:
    # Identity
    motor_id: str                              # e.g., "unitree_7520_14"
    manufacturer: str                          # e.g., "Unitree"
    model: str                                 # e.g., "7520-14"

    # 3D Assets
    step_file: Optional[str]                   # Path to STEP file
    stl_file: Optional[str]                    # Path to STL file

    # Mechanical Properties
    gear_ratio: float                          # Reduction ratio (e.g., 14.5)
    reflected_inertia: float                   # kg⋅m² (after gearbox)
    rotation_angle_range: list                 # [min, max] radians (JSON uses list for tuple)

    # Electrical Properties
    voltage_range: list                        # [min, max] V
    resistance: float                          # Ω (winding resistance)
    inductance: float                          # H (winding inductance)
    motor_constant_kt: float                   # N⋅m/A (torque constant)
    motor_constant_ke: float                   # V⋅s/rad (back-EMF constant)

    # Performance Characteristics
    stall_torque: float                        # N⋅m (at zero speed)
    peak_torque: float                         # N⋅m (instantaneous max)
    continuous_torque: float                   # N⋅m (continuous rating)
    no_load_speed: float                       # rad/s (at zero torque)
    no_load_current: float                     # A
    stall_current: float                       # A
    operating_current: float                   # A (nominal current)

    # Thermal Properties
    thermal_resistance: float                  # °C/W (junction to ambient)
    thermal_time_constant: float               # s (first-order thermal model)
    max_winding_temperature: float             # °C (safety limit)
    ambient_temperature: float                 # °C (nominal test temperature)

    # Feedback & Control
    encoder_resolution: int                    # counts/rev (post-gearing)
    encoder_type: str                          # "incremental" | "absolute"
    feedback_sensors: list                     # ["position", "velocity", "current"]
    protocol: str                              # "PWM" | "CAN" | "UART" | "EtherCAT"
    protocol_params: dict                      # Protocol-specific configuration (e.g., baudrate)

def validate_motor(file_path: str) -> bool:
    print(f"Validating {file_path}...")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to parse JSON: {e}")
        return False

    spec_fields = {f.name: f.type for f in fields(MotorSpecification)}
    required_fields = {f.name for f in fields(MotorSpecification)}
    
    # Check for missing fields
    missing = []
    for field_name in required_fields:
        if field_name not in data:
            # Check if Optional
            field_type = spec_fields[field_name]
            is_optional = str(field_type).startswith("typing.Union") or str(field_type).startswith("typing.Optional")
            if not is_optional:
                missing.append(field_name)
    
    if missing:
        print(f"  [ERROR] Missing required fields: {', '.join(missing)}")
    
    # Check for extra fields
    extra = set(data.keys()) - required_fields
    if extra:
        print(f"  [WARNING] Extra fields detected: {', '.join(extra)}")
    
    # Type checking (basic)
    type_mismatches = []
    for field_name, value in data.items():
        if field_name in spec_fields:
            # None means the extrapolator couldn't derive this field from the
            # available datasheet data. Warn rather than fail.
            if value is None:
                print(f"  [WARNING] {field_name} is None — please provide this value manually.")
                continue
            # Basic validation for common types
            field_type = spec_fields[field_name]
            if "float" in str(field_type) and not isinstance(value, (int, float)):
                type_mismatches.append(f"{field_name} (expected float, got {type(value).__name__})")
            elif "int" in str(field_type) and not isinstance(value, int):
                type_mismatches.append(f"{field_name} (expected int, got {type(value).__name__})")
            elif "str" in str(field_type) and not isinstance(value, str) and value is not None:
                type_mismatches.append(f"{field_name} (expected str, got {type(value).__name__})")
            elif "list" in str(field_type) and not isinstance(value, list):
                type_mismatches.append(f"{field_name} (expected list, got {type(value).__name__})")
            elif "dict" in str(field_type) and not isinstance(value, dict):
                type_mismatches.append(f"{field_name} (expected dict, got {type(value).__name__})")

    if type_mismatches:
        print(f"  [ERROR] Type mismatches: {', '.join(type_mismatches)}")

    success = not (missing or type_mismatches)
    if success:
        print("  [SUCCESS] Validated.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Validate motor JSON files.")
    parser.add_argument("--root", default="motor_assets", help="Root directory for motor assets")
    args = parser.parse_args()

    all_files = []
    for root, dirs, files in os.walk(args.root):
        for file in files:
            if file.endswith(".json"):
                all_files.append(os.path.join(root, file))

    if not all_files:
        print("No JSON files found to validate.")
        return

    failed_count = 0
    for file in all_files:
        if not validate_motor(file):
            failed_count += 1

    print("-" * 20)
    print(f"Validation summary: {len(all_files) - failed_count} passed, {failed_count} failed.")

    if failed_count > 0:
        exit(1)

if __name__ == "__main__":
    main()
