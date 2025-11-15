"""
Utility to setup Python path for consistent imports across the BankingBot project.
This should be imported at the top of any module that needs project-wide imports.
"""

import sys
from pathlib import Path

def setup_project_path():
    """Add the BankingBot root directory to Python path for consistent imports"""
    # Get the project root directory (BankingBot folder)
    # This function is in src/utils/, so we go up 2 levels to reach project root
    project_root = Path(__file__).parent.parent.parent
    
    # Add to Python path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root

# Automatically setup path when this module is imported
PROJECT_ROOT = setup_project_path()
