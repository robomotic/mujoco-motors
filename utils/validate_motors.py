from __future__ import annotations
import os
import json
import argparse
from dataclasses import dataclass, fields, field
from typing import Optional, Any, Tuple, List, Dict, Union

@dataclass
class MotorSpecification:
    # ============================================================================
    # REQUIRED FIELDS (physics-critical parameters)
    # ============================================================================

    # Identity (required)
    motor_id: str                              # "unitree_7520_14"
    manufacturer: str                          # "Unitree"
    model: str                                 # "7520-14"

    # Electrical Properties (required - motor-specific)
    voltage_range: Tuple[float, float]         # (min, max) V
    resistance: float                          # Ω (winding resistance)
    inductance: float                          # H (winding inductance)
    motor_constant_kt: float                   # N⋅m/A (torque constant)
    motor_constant_ke: float                   # V⋅s/rad (back-EMF constant)

    # Performance Characteristics (required - motor-specific)
    peak_torque: float                         # N⋅m (instantaneous max)
    no_load_speed: float                       # rad/s (at zero torque)

    # Thermal Properties (required - motor-specific)
    thermal_resistance: float                  # °C/W (junction to ambient)
    thermal_time_constant: float               # s (first-order model)
    max_winding_temperature: float             # °C

    # ============================================================================
    # OPTIONAL FIELDS (metadata and future enhancements)
    # ============================================================================

    # Electrical Properties (optional - additional characteristics)
    number_of_pole_pairs: Optional[int] = None
    commutation: Optional[str] = None

    # Performance Characteristics (optional - additional limits)
    max_speed: Optional[float] = None

    # 3D Assets (optional)
    step_file: Optional[str] = None
    stl_file: Optional[str] = None

    # Mechanical Properties (optional - with defaults)
    gear_ratio: float = 1.0
    reflected_inertia: float = 0.0
    rotation_angle_range: Tuple[float, float] = (-3.14159, 3.14159)
    weight: float = 0.0
    friction_static: float = 0.0
    friction_dynamic: float = 0.0

    # Performance Characteristics (optional - with defaults)
    stall_torque: float = 10.0
    continuous_torque: float = 10.0
    no_load_current: float = 0.5
    stall_current: float = 10.0
    operating_current: float = 3.0

    # Thermal Properties (optional - with defaults)
    ambient_temperature: float = 25.0

    # Feedback & Control (optional - with defaults)
    encoder_resolution: int = 2048
    encoder_type: str = "incremental"
    feedback_sensors: Optional[List[str]] = None
    protocol: str = "PWM"
    protocol_params: Optional[Dict] = None

def validate_motor(file_path: str) -> bool:
    print(f"Validating {file_path}...")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to parse JSON: {e}")
        return False

    spec_fields = {f.name: f.type for f in fields(MotorSpecification)}
    required_fields = {f.name for f in fields(MotorSpecification) if f.default == field().default}
    
    # Check for missing required fields
    missing_required = []
    for field_name in required_fields:
        if field_name not in data:
            missing_required.append(field_name)
    
    if missing_required:
        print(f"  [ERROR] Missing required fields: {', '.join(missing_required)}")
    
    # Check for extra fields
    extra = set(data.keys()) - set(spec_fields.keys())
    if extra:
        print(f"  [WARNING] Extra fields detected: {', '.join(extra)}")
    
    # Type checking and None checking
    type_mismatches = []
    for field_name, value in data.items():
        if field_name in spec_fields:
            if value is None:
                # If it's a required field, None is a warning (extrapolator couldn't find it)
                if field_name in required_fields:
                    print(f"  [WARNING] Required field '{field_name}' is null. Please provide this value manually.")
                continue
                
            field_type = spec_fields[field_name]
            field_type_str = str(field_type).lower()
            # Basic validation for common types
            if "tuple" in field_type_str or "list" in field_type_str:
                if not isinstance(value, list):
                    type_mismatches.append(f"{field_name} (expected list/tuple, got {type(value).__name__})")
            elif "dict" in field_type_str:
                if not isinstance(value, dict):
                    type_mismatches.append(f"{field_name} (expected dict, got {type(value).__name__})")
            elif "float" in field_type_str:
                if not isinstance(value, (int, float)):
                    type_mismatches.append(f"{field_name} (expected float, got {type(value).__name__})")
            elif "int" in field_type_str:
                if not isinstance(value, int):
                    type_mismatches.append(f"{field_name} (expected int, got {type(value).__name__})")
            elif "str" in field_type_str:
                if not isinstance(value, str):
                    type_mismatches.append(f"{field_name} (expected str, got {type(value).__name__})")

    if type_mismatches:
        print(f"  [ERROR] Type mismatches: {', '.join(type_mismatches)}")

    success = not (missing_required or type_mismatches)
    if success:
        print("  [SUCCESS] Validated.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Validate motor JSON files against the MotorSpecification schema.")
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
