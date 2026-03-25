import os
import json

REQUIRED_PHYSICS_FIELDS = [
    "resistance", "inductance", "motor_constant_kt", "motor_constant_ke", 
    "peak_torque", "no_load_speed", "thermal_resistance", 
    "thermal_time_constant", "max_winding_temperature"
]

CALCULATED_CANDIDATES = [
    "motor_constant_ke", "no_load_speed", "peak_torque", "stall_current", 
    "stall_torque", "rotation_angle_range"
]

def analyze_motor(file_path: str) -> str:
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return f"#### {os.path.basename(file_path)}\n- **Status**: Error reading file ({e})\n\n"
    
    motor_name = data.get("model", os.path.basename(file_path))
    status = "Validated"
    
    missing = [f for f in REQUIRED_PHYSICS_FIELDS if data.get(f) is None]
    if missing:
        status = "Validated with Warnings"
    
    # We'll assume these were calculated if they are there, as the extrapolator sets defaults or derives them
    calculated = [f for f in CALCULATED_CANDIDATES if f in data and data[f] is not None]
    
    output = f"#### {motor_name} (`{os.path.basename(file_path)}`)\n"
    output += f"- **Status**: {status}\n"
    
    if missing:
        output += f"- **Missing Required Fields**: {', '.join(missing)}\n"
    else:
        output += f"- **Missing Required Fields**: None (Complete)\n"
        
    if calculated:
        output += f"- **Derived/Calculated Fields**: {', '.join(calculated)}\n"
    
    output += "\n"
    return output

def main():
    root_dir = "motor_assets"
    if not os.path.exists(root_dir):
        print(f"{root_dir} not found.")
        return
        
    for vendor_dir in os.listdir(root_dir):
        vendor_path = os.path.join(root_dir, vendor_dir)
        if not os.path.isdir(vendor_path):
            continue
            
        info_md_path = os.path.join(vendor_path, "info.md")
        if not os.path.exists(info_md_path):
            continue
            
        with open(info_md_path, 'r') as f:
            lines = f.readlines()
            
        header = lines[0].strip() if lines else ""
        new_content = header + "\n\n"
        new_content += "### Motor Assets in this Directory\n\n"
        
        json_files = sorted([f for f in os.listdir(vendor_path) if f.endswith(".json")])
        if not json_files:
            new_content += "_No motor assets currently available for this vendor._\n"
        else:
            for json_file in json_files:
                new_content += analyze_motor(os.path.join(vendor_path, json_file))
        
        with open(info_md_path, 'w') as f:
            f.write(new_content)
        print(f"Updated {info_md_path}")

if __name__ == "__main__":
    main()
