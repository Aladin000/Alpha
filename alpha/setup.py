#!/usr/bin/env python3
"""
setup.py

Setup script for the Alpha personal finance application.
Handles environment setup, dependency installation, and initial configuration.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.10 or higher"""
    print("Checking Python version...")
    if sys.version_info < (3, 10):
        print(f"❌ Python 3.10+ required. Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        venv.create("venv", with_pip=True)
        print("✅ Virtual environment created")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("Installing dependencies...")
    try:
        # Determine the correct pip path based on OS
        if os.name == 'nt':  # Windows
            pip_path = Path("venv/Scripts/pip")
        else:  # Unix/Linux/macOS
            pip_path = Path("venv/bin/pip")
        
        subprocess.run([
            str(pip_path), "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_database():
    """Initialize the SQLite database"""
    print("Initializing database...")
    try:
        import sqlite3
        conn = sqlite3.connect("alpha.db")
        conn.execute("SELECT 1")  # Simple test query
        conn.close()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def verify_installation():
    """Run dependency tests to verify installation"""
    print("Verifying installation...")
    try:
        # Determine the correct python path based on OS
        if os.name == 'nt':  # Windows
            python_path = Path("venv/Scripts/python")
        else:  # Unix/Linux/macOS
            python_path = Path("venv/bin/python")
        
        result = subprocess.run([
            str(python_path), "test_dependencies.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "All dependencies are working correctly!" in result.stdout:
            print("✅ Installation verified successfully")
            return True
        else:
            print("❌ Installation verification failed")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def create_launcher():
    """Create a launcher script"""
    print("Creating launcher script...")
    try:
        # Determine the correct paths based on OS
        if os.name == 'nt':  # Windows
            launcher_content = f"""@echo off
cd /d "{os.getcwd()}"
venv\\Scripts\\python.exe alpha.py
pause
"""
            launcher_path = "launch_alpha.bat"
        else:  # Unix/Linux/macOS
            launcher_content = f"""#!/bin/bash
cd "{os.getcwd()}"
source venv/bin/activate
python alpha.py
"""
            launcher_path = "launch_alpha.sh"
        
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(launcher_path, 0o755)
        
        print(f"✅ Launcher created: {launcher_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create launcher: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("ALPHA SETUP")
    print("=" * 60)
    print()
    
    setup_steps = [
        ("Python Version Check", check_python_version),
        ("Virtual Environment", create_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Database", create_database),
        ("Verification", verify_installation),
        ("Launcher", create_launcher),
    ]
    
    all_success = True
    for step_name, step_func in setup_steps:
        print(f"--- {step_name} ---")
        success = step_func()
        if not success:
            all_success = False
            print(f"❌ {step_name} failed!")
            break
        print()
    
    print("=" * 60)
    if all_success:
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print()
        print("Alpha is ready to use!")
        print("You can now run the application using:")
        if os.name == 'nt':
            print("  • Double-click: launch_alpha.bat")
            print("  • Command line: launch_alpha.bat")
        else:
            print("  • Command line: ./launch_alpha.sh")
            print("  • Or activate venv and run: python alpha.py")
        print()
        print("For offline use:")
        print("  • All dependencies are installed locally")
        print("  • Database is SQLite (no network required)")
        print("  • Configuration available in config.yaml")
    else:
        print("❌ SETUP FAILED!")
        print("Please check the error messages above and try again.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 