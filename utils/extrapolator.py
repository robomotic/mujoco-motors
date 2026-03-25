"""
extrapolator.py
Extrapolates missing MotorSpecification fields in a motor JSON file using
standard electromechanical formulas.

Usage:
    python3 utils/extrapolator.py --input motor_assets/maxon/maxon_ec_i_40_488607.json
    python3 utils/extrapolator.py --input motor_assets/maxon/maxon_ec_i_40_488607.json --dry-run
    python3 utils/extrapolator.py --all --root motor_assets
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
    Given a (possibly incomplete) motor data dict, compute and fill in any
    missing fields using the standard formulas below.

    Returns:
        updated  : dict with newly derived fields added
        derived  : list of field names that were computed in this call
    """
    updated = copy.deepcopy(data)
    derived = []

    def _get(key):
        return updated.get(key)

    # ------------------------------------------------------------------
    # Back-EMF constant  Ke = 1 / (Kn * 0.1047)
    #   Kn is the speed constant in RPM/V.
    #   In SI units Ke ≈ Kt, so we also accept motor_constant_kt as a
    #   fallback when Kn is unavailable.
    # ------------------------------------------------------------------
    if _get("motor_constant_ke") is None:
        kn = _get("speed_constant_kn")          # RPM/V  (optional source field)
        kt = _get("motor_constant_kt")
        if kn is not None:
            ke = 1.0 / (kn * 0.10471975511965977)
            updated["motor_constant_ke"] = round(ke, 6)
            derived.append("motor_constant_ke")
            print(f"  [DERIVED] motor_constant_ke = {updated['motor_constant_ke']:.6f}  (from speed_constant_kn)")
        elif kt is not None:
            # In SI, Ke ≈ Kt
            updated["motor_constant_ke"] = kt
            derived.append("motor_constant_ke")
            print(f"  [DERIVED] motor_constant_ke = {updated['motor_constant_ke']:.6f}  (assumed ≈ Kt)")

    # ------------------------------------------------------------------
    # Nominal voltage: use midpoint of voltage_range if not explicit
    # ------------------------------------------------------------------
    v_nom = _get("voltage_nominal")
    if v_nom is None:
        vrange = _get("voltage_range")
        if vrange and len(vrange) == 2:
            v_nom = vrange[1]   # use max voltage as nominal

    # ------------------------------------------------------------------
    # Stall current  Is = V_nom / R
    # ------------------------------------------------------------------
    if _get("stall_current") is None:
        r = _get("resistance")
        if v_nom is not None and r is not None and r > 0:
            stall_i = v_nom / r
            updated["stall_current"] = round(stall_i, 4)
            derived.append("stall_current")
            print(f"  [DERIVED] stall_current = {updated['stall_current']:.4f} A  (V_nom={v_nom}, R={r})")

    # ------------------------------------------------------------------
    # Stall torque  τs = Is * Kt
    # ------------------------------------------------------------------
    if _get("stall_torque") is None:
        stall_i = _get("stall_current")
        kt = _get("motor_constant_kt")
        if stall_i is not None and kt is not None:
            stall_t = stall_i * kt
            updated["stall_torque"] = round(stall_t, 6)
            derived.append("stall_torque")
            print(f"  [DERIVED] stall_torque = {updated['stall_torque']:.6f} N·m")

    # ------------------------------------------------------------------
    # Peak torque: default to stall_torque when not provided
    # ------------------------------------------------------------------
    if _get("peak_torque") is None:
        stall_t = _get("stall_torque")
        if stall_t is not None:
            updated["peak_torque"] = stall_t
            derived.append("peak_torque")
            print(f"  [DERIVED] peak_torque = {updated['peak_torque']:.6f} N·m  (assumed = stall_torque)")

    # ------------------------------------------------------------------
    # No-load speed  ω_nl = V_nom * Kn   →  rad/s
    #   Or:          ω_nl = V_nom / Ke
    # ------------------------------------------------------------------
    if _get("no_load_speed") is None:
        kn = _get("speed_constant_kn")
        ke = _get("motor_constant_ke")
        if v_nom is not None and kn is not None:
            omega = v_nom * kn * 0.10471975511965977   # convert RPM → rad/s
            updated["no_load_speed"] = round(omega, 4)
            derived.append("no_load_speed")
            print(f"  [DERIVED] no_load_speed = {updated['no_load_speed']:.4f} rad/s  (from Kn)")
        elif v_nom is not None and ke is not None and ke > 0:
            omega = v_nom / ke
            updated["no_load_speed"] = round(omega, 4)
            derived.append("no_load_speed")
            print(f"  [DERIVED] no_load_speed = {updated['no_load_speed']:.4f} rad/s  (from Ke)")

    # ------------------------------------------------------------------
    # Thermal resistance  R_th_total = R_th_w-h + R_th_h-a
    # ------------------------------------------------------------------
    if _get("thermal_resistance") is None:
        r_wh = _get("thermal_resistance_winding_housing")
        r_ha = _get("thermal_resistance_housing_ambient")
        if r_wh is not None and r_ha is not None:
            updated["thermal_resistance"] = round(r_wh + r_ha, 4)
            derived.append("thermal_resistance")
            print(f"  [DERIVED] thermal_resistance = {updated['thermal_resistance']:.4f} °C/W  (R_wh + R_ha)")

    # ------------------------------------------------------------------
    # Defaults for mandatory fields that cannot be computed
    # ------------------------------------------------------------------
    DEFAULTS = {
        "rotation_angle_range":      [0, 0],
        "thermal_resistance":        None,
        "thermal_time_constant":     None,
        "max_winding_temperature":   None,
        "ambient_temperature":       25.0,
        "encoder_resolution":        0,
        "encoder_type":              "unknown",
        "feedback_sensors":          [],
        "protocol":                  "unknown",
        "protocol_params":           {},
        "operating_current":         None,
    }
    for key, default in DEFAULTS.items():
        if _get(key) is None:
            updated[key] = default
            derived.append(key)
            if default is not None:
                print(f"  [DEFAULT] {key} = {default}")
            else:
                warnings.warn(
                    f"Field '{key}' could not be derived and has no default. "
                    "Please provide it manually.",
                    stacklevel=2,
                )

    return updated, derived


# ---------------------------------------------------------------------------
# File-level helpers
# ---------------------------------------------------------------------------

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
        print(f"  [DRY-RUN] Would add/fill {len(derived)} field(s): {', '.join(derived)}")
    else:
        with open(path, "w") as f:
            json.dump(updated, f, indent=4)
        print(f"  [SAVED] {len(derived)} field(s) added: {', '.join(derived)}")

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extrapolate missing MotorSpecification fields using electromechanical formulas."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input", "-i",
        help="Path to a single motor JSON file to process."
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all motor JSON files under --root."
    )

    parser.add_argument(
        "--root",
        default="motor_assets",
        help="Root directory for motor assets (used with --all). Default: motor_assets"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing files."
    )

    args = parser.parse_args()

    if args.input:
        process_file(args.input, dry_run=args.dry_run)
    else:
        json_files = []
        for root, _dirs, files in os.walk(args.root):
            for fname in files:
                if fname.endswith(".json"):
                    json_files.append(os.path.join(root, fname))

        if not json_files:
            print(f"No JSON files found under '{args.root}'.")
            return

        for path in json_files:
            process_file(path, dry_run=args.dry_run)

        print("\nDone.")


if __name__ == "__main__":
    main()
