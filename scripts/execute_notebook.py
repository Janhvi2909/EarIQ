"""Execute the delivered notebook in this project's Python environment."""
import os
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
for name, suffix in [("JUPYTER_RUNTIME_DIR","jupyter/runtime"),("JUPYTER_DATA_DIR","jupyter/data"),("IPYTHONDIR","ipython"),("MPLCONFIGDIR","matplotlib")]:
    folder=ROOT/".cache"/suffix
    folder.mkdir(parents=True,exist_ok=True)
    os.environ[name]=str(folder)
os.environ["PATH"]=str(Path(sys.executable).parent)+os.pathsep+os.environ.get("PATH","")
path=ROOT/"notebooks/M2_EDA.ipynb"
notebook=nbformat.read(path,as_version=4)
NotebookClient(notebook,timeout=180,kernel_name="python3",resources={"metadata":{"path":str(ROOT)}}).execute()
nbformat.write(notebook,path)
print("Executed all notebook cells successfully.")
