import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PIPELINE_SCRIPTS = [
    "01_citibike_h3_cells.py",
    "02_census_and_emp_data.py",
    "03_nyc_open_data.py",
    "04_merge_data.py"
]

def run_pipeline():
    for script in PIPELINE_SCRIPTS:
        if not os.path.exists(script):
            print(f"Skipping {script} - file not found")
            continue
                    
        result = subprocess.run([sys.executable, script])
        if result.returncode == 0:
            print(f"Completed {script}")
        else:
            print(f"Error: {script} failed with exit code {result.returncode}. Aborting.")
            sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
