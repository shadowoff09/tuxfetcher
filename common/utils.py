"""Common utility functions"""

import subprocess
from typing import List
from .colors import Colors


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with a default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def update_repositories() -> bool:
    """Update package repositories"""
    try:
        print(f"\n{Colors.BLUE}🔄 Updating package repositories...{Colors.ENDC}")
        run_command(["sudo", "apt-get", "update"])
        print(f"\n{Colors.GREEN}✅ Repositories updated successfully!{Colors.ENDC}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Failed to update repositories: {str(e)}{Colors.ENDC}")
        return False

def update_system() -> bool:
    """Update system packages"""
    try:
        print(f"\n{Colors.BLUE}🔄 Updating system packages...{Colors.ENDC}")
        
        # Update package list
        run_command(["sudo", "apt-get", "update"])
        # Upgrade packages
        run_command(["sudo", "apt-get", "upgrade", "-y"])
        
        print(f"\n{Colors.GREEN}✅ System updated successfully!{Colors.ENDC}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Failed to update system: {str(e)}{Colors.ENDC}")
        return False 
    
    
    
def install_packages(packages: List[str]) -> bool:
    """Install a list of packages"""
    try:
        print(f"\n{Colors.BLUE}🚀 Installing packages: {', '.join(packages)}{Colors.ENDC}")
        
        for package in packages:
            run_command(["sudo", "apt-get", "install", "-y", package])
        
        print(f"\n{Colors.GREEN}✅ Packages installed successfully!{Colors.ENDC}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Failed to install packages: {str(e)}{Colors.ENDC}")
        return False
    
    
def remove_packages(packages: List[str]) -> bool:
    """Remove a list of packages"""
    try:
        print(f"\n{Colors.BLUE}🗑️ Removing packages: {', '.join(packages)}{Colors.ENDC}")
        
        for package in packages:
            run_command(["sudo", "apt-get", "remove", "-y", package])
            run_command(["sudo", "apt-get", "autoremove", "-y"])
        
        print(f"\n{Colors.GREEN}✅ Packages removed successfully!{Colors.ENDC}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Failed to remove packages: {str(e)}{Colors.ENDC}")
        return False
    
def run_command(command: List[str]) -> bool:
    """Run a command with subprocess and print its output in real-time"""
    try:
        subprocess.run(
            command,
            check=True,
            stdout=None,  # Directly print to console
            stderr=None   # Directly print to console
        )
        return True
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Command failed: {str(e)}{Colors.ENDC}")
        return False
    
def wait_for_enter():
    """Wait for user to press Enter"""
    input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")