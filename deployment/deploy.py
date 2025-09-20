#!/usr/bin/env python3
"""
Deployment script for PythonAnywhere
"""
import os
import shutil
import subprocess
import sys

def run_command(command, check=True):
    """Run a shell command"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result

def create_directories():
    """Create necessary directories"""
    dirs = ['logs', 'temp']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"Created directory: {dir_name}")

def install_requirements():
    """Install production requirements"""
    print("Installing production requirements...")
    run_command("pip install -r deployment/requirements-prod.txt")

def setup_environment(env_type='production'):
    """Setup environment variables"""
    if env_type == 'production':
        source_file = 'deployment/env.example'
        target_file = '.env'
        print("Setting up production environment...")
    else:
        source_file = 'deployment/env.dev'
        target_file = '.env'
        print("Setting up development environment...")
    
    if not os.path.exists(target_file):
        if os.path.exists(source_file):
            print(f"Creating {target_file} file from {source_file}...")
            shutil.copy(source_file, target_file)
            print(f"Please edit {target_file} file with your values")
        else:
            print(f"Warning: {source_file} not found. Please create {target_file} manually.")
    else:
        print(f"{target_file} file already exists")

def main():
    """Main deployment function"""
    print("Starting deployment setup...")
    
    # Check if user wants development or production
    if len(sys.argv) > 1 and sys.argv[1] == 'dev':
        env_type = 'development'
        print("Setting up for development environment")
    else:
        env_type = 'production'
        print("Setting up for production environment")
    
    try:
        create_directories()
        setup_environment(env_type)
        
        if env_type == 'production':
            install_requirements()
        
        print(f"\n{env_type.capitalize()} setup completed!")
        print(f"\nNext steps:")
        
        if env_type == 'production':
            print("1. Edit .env file with your production values")
            print("2. Set SECRET_KEY to a secure random string")
            print("3. Configure your PythonAnywhere web app to use deployment/wsgi.py")
            print("4. Set the working directory to your project folder")
            print("5. Set the WSGI configuration file to deployment/wsgi.py")
        else:
            print("1. Edit .env file if needed")
            print("2. Run 'python app.py' to start development server")
            print("3. Your app will be available at http://localhost:5000")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during deployment: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
