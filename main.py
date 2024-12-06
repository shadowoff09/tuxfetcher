import os
import sys
import subprocess
from bind import install_bind, uninstall_bind
from webmin import install_webmin, uninstall_webmin
from common.colors import Colors


def print_header():
    """Print the application header"""
    os.system('clear')
    print(f"{Colors.BLUE}{Colors.BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║             🐧 TuxFetcher CLI              ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")


def check_bind_status() -> tuple[bool, str]:
    """Check if BIND DNS Server is running and get its PID"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "bind9"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip() == "active":
            # Get PID
            pid_result = subprocess.run(
                ["systemctl", "show", "--property=MainPID", "bind9"],
                capture_output=True,
                text=True
            )
            pid = pid_result.stdout.split('=')[1].strip()
            return True, pid
        return False, ""
    except Exception:
        return False, ""


def check_webmin_status() -> tuple[bool, str]:
    """Check if Webmin is running and get its PID"""
    try:
        # First try using systemctl
        result = subprocess.run(
            ["systemctl", "is-active", "webmin"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip() == "active":
            # Get PID from systemctl
            pid_result = subprocess.run(
                ["systemctl", "show", "--property=MainPID", "webmin"],
                capture_output=True,
                text=True
            )
            pid = pid_result.stdout.split('=')[1].strip()
            if pid != "0":
                return True, pid
        
        # If systemctl didn't work, try checking the process directly
        ps_result = subprocess.run(
            ["pgrep", "-f", "miniserv.pl"],
            capture_output=True,
            text=True
        )
        if ps_result.stdout:
            return True, ps_result.stdout.strip()
        
        return False, ""
    except Exception:
        return False, ""


def print_status():
    """Print current status of services"""
    print(f"\n{Colors.BOLD}System Status:{Colors.ENDC}")
    
    # Check BIND status
    bind_running, bind_pid = check_bind_status()
    if bind_running:
        print(f"{Colors.GREEN}● BIND DNS Server is running (PID: {bind_pid}){Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}○ BIND DNS Server is not running{Colors.ENDC}")
    
    # Check Webmin status
    webmin_running, webmin_pid = check_webmin_status()
    if webmin_running:
        print(f"{Colors.GREEN}● Webmin is running (PID: {webmin_pid}){Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}○ Webmin is not running{Colors.ENDC}")
    
    print(f"{Colors.HEADER}{Colors.BOLD}{'═' * 40}{Colors.ENDC}")


def print_category(name: str):
    """Print a category header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'═' * 15} {name} {'═' * 15}{Colors.ENDC}")


def print_menu():
    """Print the main menu"""
    print_status()
    
    print_category("DNS Server")
    print(f"{Colors.WHITE}1.{Colors.ENDC} Install BIND DNS Server")
    print(f"{Colors.WHITE}2.{Colors.ENDC} Uninstall BIND DNS Server")
    
    print_category("Webmin")
    print(f"{Colors.WHITE}3.{Colors.ENDC} Install Webmin")
    print(f"{Colors.WHITE}4.{Colors.ENDC} Uninstall Webmin")
    
    print(f"\n{Colors.WHITE}0.{Colors.ENDC} Exit")
    print(f"{Colors.HEADER}{Colors.BOLD}{'═' * 40}{Colors.ENDC}")


def handle_choice(choice: str):
    """Handle user menu choice"""
    try:
        if choice == "1":
            install_bind()
        elif choice == "2":
            uninstall_bind()
        elif choice == "3":
            install_webmin()
        elif choice == "4":
            uninstall_webmin()
        elif choice == "0":
            print(f"\n{Colors.GREEN}👋 Thank you for using TuxFetcher!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.FAIL}❌ Invalid choice. Please try again.{Colors.ENDC}")
        
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ An error occurred: {str(e)}{Colors.ENDC}")
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")


def main():
    """Main application loop"""
    while True:
        print_header()
        print_menu()
        choice = input(f"\n{Colors.BOLD}Enter your choice (0-4): {Colors.ENDC}")
        handle_choice(choice)


if __name__ == "__main__":
    main()
