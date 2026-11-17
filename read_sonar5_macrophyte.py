import pandas as pd
import re
import glob
import os


def read_sonar5_macrophyte(file_path: str) -> pd.DataFrame:
    """
    Read a Sonar5-Pro macrophyte analysis .txt file into a pandas DataFrame.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sep_pattern = re.compile(r"^-{3,}\s*$")
    sep_index = None
    metadata = {}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if sep_pattern.match(stripped):
            sep_index = i
            break
        match = re.match(r"^(\w[\w\s\.]*?)=(.*)", stripped)
        if match:
            metadata[match.group(1).strip()] = match.group(2).strip()

    if sep_index is None:
        raise ValueError("Could not find the separator line (---...) in the file.")

    expected_cols = [
        "From_ping", "To_ping", "Analysed_ping", "Nr_heights_accepted",
        "From_pos_N", "Center_pos_N", "To_pos_N",
        "From_pos_E", "Center_pos_E", "To_pos_E",
        "Sailed_Dist_m", "Boat_speed_m_s",
        "Mean_base_depth_m", "Max_base_depth_m",
        "Mean_BioHeight_m", "Max_BioHeight_m",
        "BioArea_m2", "BioVolume_m3",
        "PAI_%", "PVI_%",
        "Mean_Sv_dB", "sA_m2_ha",
        "Investigated_area", "Mean_bottom_depth_m",
    ]

    data_lines = lines[sep_index + 3:]
    records = []
    current_file = None

    for line in data_lines:
        parts = line.split()
        if not parts:
            continue

        if len(parts) == 25:
            current_file = parts[0]
            values = parts[1:]
        elif len(parts) == 24:
            values = parts
        else:
            continue

        record = {}
        if current_file:
            record["File"] = current_file

        for i, col in enumerate(expected_cols):
            val = values[i] if i < len(values) else None
            if val is not None:
                try:
                    record[col] = float(val)
                except ValueError:
                    record[col] = val
            else:
                record[col] = None

        records.append(record)

    df = pd.DataFrame(records, columns=["File"] + expected_cols)
    df.attrs["metadata"] = metadata
    return df


def process_all_files(input_dir: str, output_csv: str):
    """
    Read all Sonar5-Pro macrophyte .txt files in a directory,
    extract File, From_pos_N, To_pos_N, and Mean_BioHeight_m,
    and save to a single CSV.

    Parameters
    ----------
    input_dir : str
        Directory containing the .txt files.
    output_csv : str
        Path for the output .csv file.
    """

    # Find all .txt files in the directory
    pattern = os.path.join(input_dir, "*.txt")
    txt_files = glob.glob(pattern)

    if not txt_files:
        print(f"No .txt files found in: {input_dir}")
        return

    all_rows = []

    for txt_file in txt_files:
        print(f"Processing: {os.path.basename(txt_file)}")
        df = read_sonar5_macrophyte(txt_file)

        # Extract only the columns we need
        selected = df[["File", "To_pos_N", "To_pos_E", "Mean_BioHeight_m"]].copy()

        # Add the source file name (without extension) for reference
        selected["Source_file"] = os.path.basename(txt_file)

        all_rows.append(selected)

    # Combine all rows into one DataFrame
    combined = pd.concat(all_rows, ignore_index=True)

    # Save to CSV
    combined.to_csv(output_csv, index=False)
    print(f"\nSaved {len(combined)} rows to: {output_csv}")


if __name__ == "__main__":
    # Set your input directory and output file path   **BE SURE TO CHANGE DIRECTORY IF LOOKING AT A DIFFERENT RIVER**
    INPUT_DIR = r"D:\Eelgrass2026\Dunk\macro_data\aug7"
    OUTPUT_CSV = r"D:\Eelgrass2026\Dunk\macro_data\aug7\macrophyte_summary.csv"

    process_all_files(INPUT_DIR, OUTPUT_CSV)
