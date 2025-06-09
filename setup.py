#!/usr/bin/env python3
"""
NewsBreeze Setup Script
Automated setup for the NewsBreeze application
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   NewsBreeze requires Python 3.8 or higher")
        return False

def create_virtual_environment():
    """Create a virtual environment"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def activate_and_install():
    """Activate virtual environment and install dependencies"""
    system = platform.system()
    
    if system == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install dependencies
    install_cmd = f"{pip_cmd} install -r requirements.txt"
    return run_command(install_cmd, "Installing dependencies")

def create_directories():
    """Create necessary directories"""
    directories = [
        "static/audio",
        "static/voices",
        "templates"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def download_models():
    """Download AI models (this will happen on first run)"""
    print("📦 AI models will be downloaded automatically on first run")
    print("   This may take several minutes depending on your internet connection")
    return True

def main():
    """Main setup function"""
    print("🎙️ NewsBreeze Setup Script")
    print("=" * 50)
    print("This script will set up NewsBreeze on your system")
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Checking Python version", lambda: True),  # Already checked
        ("Creating virtual environment", create_virtual_environment),
        ("Installing dependencies", activate_and_install),
        ("Creating directories", create_directories),
        ("Preparing AI models", download_models),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n🔧 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 50)
    
    if not failed_steps:
        print("🎉 Setup completed successfully!")
        print()
        print("📋 Next steps:")
        print("1. Activate the virtual environment:")
        
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        print("2. Start NewsBreeze:")
        print("   python run.py")
        print()
        print("3. Open your browser and go to:")
        print("   http://localhost:8000")
        print()
        print("🧪 To test the installation:")
        print("   python test_app.py")
        
    else:
        print("⚠️  Setup completed with some issues:")
        for step in failed_steps:
            print(f"   - {step}")
        print()
        print("💡 Please check the error messages above and try again")
        print("   You may need to install dependencies manually")
    
    return len(failed_steps) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 