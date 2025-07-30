#!/usr/bin/env python3
"""
Setup script for the Signup Bot.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header():
    """Print the setup header."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 SIGNUP BOT SETUP WIZARD                     ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_python_version():
    """Check if the Python version is 3.10 or higher."""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required.")
        sys.exit(1)
    print("✓ Python version is compatible.")

def create_virtualenv():
    """Create a virtual environment if it doesn't exist."""
    venv_dir = Path("venv")
    if not venv_dir.exists():
        print("\nCreating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("✓ Virtual environment created.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            sys.exit(1)
    else:
        print("✓ Virtual environment already exists.")

def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling dependencies...")
    pip_cmd = ["venv/bin/pip"] if os.name != 'nt' else ["venv\\Scripts\\pip"]
    
    try:
        subprocess.run([*pip_cmd, "install", "--upgrade", "pip"], check=True)
        subprocess.run([*pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Set up the environment variables."""
    print("\nSetting up environment variables...")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        shutil.copy(".env.example", ".env")
        print("✓ Created .env file from .env.example")
    else:
        print("✓ .env file already exists.")
    
    print("\nPlease edit the .env file with your configuration.")
    print("Required settings:")
    print("1. DISCORD_TOKEN - Your Discord bot token")
    print("2. FIREBASE_CRED - Base64 encoded Firebase credentials")
    print("3. AUTH - Your Clash of Clans API token")

def main():
    """Run the setup process."""
    print_header()
    check_python_version()
    create_virtualenv()
    install_dependencies()
    setup_environment()
    
    print("""
🎉 Setup completed successfully! Next steps:
1. Edit the .env file with your configuration
2. Run the bot: python run.py
3. In a separate terminal, run the API: python run_api.py

Or use Docker Compose:
docker-compose up --build
""")

if __name__ == "__main__":
    main()
