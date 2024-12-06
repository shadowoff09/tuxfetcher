"""Common utility functions"""

import subprocess
import time
from typing import List
from tqdm import tqdm
from .colors import Colors


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with a default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_user_output_preference() -> bool:
    """Ask user if they want to see detailed command output"""
    print("\nDo you want to see detailed command output? (y/n): ", end="")
    show_output = input().lower().strip() == "y"
    
    if show_output:
        print("\n⚠️  Detailed command output will be shown.")
    else:
        print("\n⚠️  Only progress bars will be shown.")
    
    return show_output


def run_command_with_progress(
    command: List[str],
    description: str,
    duration: int,
    show_output: bool = False
) -> subprocess.CompletedProcess:
    """Run a command with a progress bar"""
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        with tqdm(
            total=100,
            desc=description,
            bar_format='{desc:<25} |{bar:30}| {percentage:3.0f}% {postfix}',
            unit='%'
        ) as pbar:
            
            start_time = time.time()
            last_progress = 0
            
            while process.poll() is None:
                if show_output:
                    output = process.stdout.readline()
                    if output:
                        tqdm.write(output.strip())
                
                elapsed = time.time() - start_time
                progress = min(100, int((elapsed / duration) * 100))
                
                if progress > last_progress:
                    pbar.update(progress - last_progress)
                    last_progress = progress
                
                time.sleep(0.1)
            
            # Get final output
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                if show_output and stderr:
                    tqdm.write(f"Error: {stderr}")
                raise subprocess.CalledProcessError(
                    process.returncode,
                    command,
                    stdout,
                    stderr
                )
            
            # Complete progress bar
            pbar.update(100 - last_progress)
            pbar.postfix = "✓"
        
        return subprocess.CompletedProcess(
            command,
            process.returncode,
            stdout,
            stderr
        )
        
    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.FAIL}❌ Command failed: {str(e)}{Colors.ENDC}")
        if show_output and e.stderr:
            print(f"Error details:\n{e.stderr}")
        raise
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Unexpected error: {str(e)}{Colors.ENDC}")
        raise


def update_system(show_output: bool = False) -> bool:
    """Update system packages"""
    try:
        print("\n🔄 Updating system packages...")
        
        # Update package list
        run_command_with_progress(
            ["sudo", "apt-get", "update"],
            "Updating package list",
            5,
            show_output
        )
        
        # Upgrade packages
        run_command_with_progress(
            ["sudo", "apt-get", "upgrade", "-y"],
            "Upgrading packages",
            10,
            show_output
        )
        
        print(f"\n{Colors.GREEN}✅ System updated successfully!{Colors.ENDC}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Failed to update system: {str(e)}{Colors.ENDC}")
        return False 