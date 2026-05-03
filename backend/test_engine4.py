import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.api import get_all_tasks
print(get_all_tasks())
