"""
extrapolator.py
Extrapolates missing MotorSpecification fields in a motor JSON file using
standard electromechanical formulas. Updated for the new MotorSpecification schema.
"""

from __future__ import annotations
import os
import json
import argparse
import warnings
import copy
from typing import Tuple, List

# ---------------------------------------------------------------------------
# Formulas
# ---------------------------------------------------------------------------

def extrapolate(data: dict) -> Tuple[dict, List[str]]:
    """
    Given a motor data dict, compute and fill in missing fields using formulas.
    """
    updated = copy.deepcopy(data)
    derived = []

    def _get(key):
        return updated.get(key)

    # ------------------------------------------------------------------
    # Nominal voltage max for derivations
    # ------------------------------------------------------------------
    vrange = _get("voltage_range")
    v_max = vrange[1] if vrange and len(vrange) == 2 else _get("voltage_nominal")

    # 1. Back-EMF constant (required)
    if _get("motor_constant_ke") is None:
        kt = _get("motor_constant_kt")
        if kt is not None:
            updated["motor_constant_ke"] = kt
            derived.append("motor_constant_ke")
            print(f"  [DERIVED] motor_constant_ke = {updated['motor_constant_ke']:.6f} (assumed ≈ Kt)")

    # 2. No-load speed (required)
    if _get("no_load_speed") is None:
        ke = _get("motor_constant_ke")
        if v_max is not None and ke is not None and ke > 0:
            updated["no_load_speed"] = round(v_max / ke, 4)
            derived.append("no_load_speed")
            print(f"  [DERIVED] no_load_speed = {updated['no_load_speed']:.4f} rad/s")

    # 3. Peak Torque (required)
    if _get("peak_torque") is None:
        st = _get("stall_torque")
        if st is not None:
            updated["peak_torque"] = st
            derived.append("peak_torque")
            print(f"  [DERIVED] peak_torque = {updated['peak_torque']:.6f} (assumed = stall_torque)")

    # ------------------------------------------------------------------
    # Apply Schema Defaults for Optional/Metadata Fields
    # ------------------------------------------------------------------
    
    # Defaults according to new MotorSpecification
    DEFAULTS = {
        # Required but may need manual input (marked None)
        "thermal_resistance":        None,
        "thermal_time_constant":     None,
        "max_winding_temperature":   None,
        
        # Optional with specified defaults
        "gear_ratio":                1.0,
        "reflected_inertia":         0.0,
        "rotation_angle_range":      [-3.14159, 3.14159],
        "weight":                    0.0,
        "friction_static":           0.0,
        "friction_dynamic":          0.0,
        "stall_torque":              10.0,
        "continuous_torque":         10.0,
        "no_load_current":           0.5,
        "stall_current":             10.0,
        "operating_current":         3.0,
        "ambient_temperature":       25.0,
        "encoder_resolution":        2048,
        "encoder_type":              "incremental",
        "protocol":                  "PWM",
        
        # Identity (required but must be provided)
        "motor_id":                  "unknown",
        "manufacturer":              "unknown",
        "model":                     "unknown",
    }

    for key, default in DEFAULTS.items():
        if key not in updated or updated[key] is None:
            updated[key] = default
            derived.append(key)
            if default is not None:
                print(f"  [DEFAULT] {key} = {default}")
            else:
                warnings.warn(f"Required field '{key}' is missing or None and could not be derived.")

    return updated, derived

def process_file(path: str, dry_run: bool = False) -> bool:
    print(f"\nProcessing: {path}")
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Cannot read file: {e}")
        return False

    updated, derived = extrapolate(data)
    if not derived:
        print("  [OK] No missing fields detected.")
        return True

    if dry_run:
        print(f"  [DRY-RUN] Would add/fill {len(derived)} field(s)")
    else:
        with open(path, "w") as f:
            json.dump(updated, f, indent=4)
        print(f"  [SAVED] {len(derived)} field(s) updated.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Extrapolate missing MotorSpecification fields.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", "-i", help="Path to single motor JSON.")
    group.add_argument("--all", action="store_true", help="Process all JSONs.")
    parser.add_argument("--root", default="motor_assets", help="Root search directory.")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to disk.")
    args = parser.parse_args()

    if args.input:
        process_file(args.input, args.dry_run)
    else:
        for root, _, files in os.walk(args.root):
            for file in files:
                if file.endswith(".json"):
                    process_file(os.path.join(root, file), args.dry_run)
    print("\nDone.")

if __name__ == "__main__":
    main()
