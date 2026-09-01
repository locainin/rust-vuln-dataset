import sys
from pathlib import Path


DATASET_ROOT = Path(__file__).resolve().parents[2]
if str(DATASET_ROOT) not in sys.path:
    sys.path.insert(0, str(DATASET_ROOT))
