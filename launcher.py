import subprocess
import sys
from pathlib import Path

script = Path(__file__).parent / 'scripts' / 'start.py'
subprocess.run([sys.executable, str(script)])
