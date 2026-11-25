"""Offline rebuild after acquisition. Uses current interpreter for every step."""
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for filename in ["prepare_data.py","analyse_data.py","build_deliverables.py","execute_notebook.py"]:
    print(f"Running {filename}",flush=True)
    subprocess.run([sys.executable,str(ROOT/"scripts"/filename)],cwd=ROOT,check=True)
subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-v"],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(ROOT/"scripts/verify_data.py")],cwd=ROOT,check=True)
