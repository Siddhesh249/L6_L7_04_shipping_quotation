import json

def calculate_dimensional_weight(dimensions_str):
    dims = dimensions_str.split('x')
    length = float(dims[0])
    width = float(dims[1])
    height = float(dims[2])
    return round((length * width * height) / 5000.0, 2)

def format_tracking_label(raw_code):
    prefix = raw_code[0].upper()
    tracking_num = int(raw_code[1:])
    return f"{prefix}-{tracking_num:06d}"

def parse_package_manifest(json_payload):
    data = json.loads(json_payload)
    return float(data["weight"])

def main():
    print("==== Running calculate_dimensional_weight ====")
    dims_input = input("Enter dimensions LxWxH in cm (e.g. 20x30x10): ")
    dim_weight = calculate_dimensional_weight(dims_input)
    print("Dimensional Weight (kg):", dim_weight)

    print("\n==== Running format_tracking_label ====")
    code_input = input("Enter raw code (e.g. E123): ")
    label = format_tracking_label(code_input)
    print("Formatted Label:", label)

    print("\n==== Running parse_package_manifest ====")
    json_input = input('Enter manifest JSON (e.g. {"weight": 12.5}): ')
    weight = parse_package_manifest(json_input)
    print("Manifest Weight:", weight)

if __name__ == "__main__":
    main()