import os
import sys
import platform
from webmin import install_webmin, uninstall_webmin, stop_webmin_service, start_webmin_service, restart_webmin_service, check_webmin_status
from common.utils import wait_for_enter
from common.colors import Colors

def check_admin_privileges():
    """Check if the script is run with admin privileges"""
    if os.geteuid() != 0:
        print(f"\n{Colors.FAIL}❌ This script must be run as root. Please try again with 'sudo'.{Colors.ENDC}\n")
        sys.exit(1)

def check_linux_os():
    """Check if the script is running on a Linux system"""
    if platform.system() != "Linux":
        print(f"\n{Colors.FAIL}❌ This script is intended to run on Linux systems only.{Colors.ENDC}\n")
        sys.exit(1)

def print_header():
    """Print the application header"""
    os.system('clear')
    print(f"{Colors.BLUE}{Colors.BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║             🐧 TuxFetcher CLI              ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

def print_category(name: str):
    """Print a category header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'═' * 15} {name} {'═' * 15}{Colors.ENDC}")


def print_menu():
    """Print the main menu"""
    print_category("Main Menu")
    print(f"{Colors.BLUE}1.{Colors.ENDC} Webmin Management")
    print(f"{Colors.BLUE}2.{Colors.ENDC} [Other Main Option]")
    
    print(f"\n{Colors.RED}0.{Colors.ENDC} Exit")
    print(f"{Colors.HEADER}{Colors.BOLD}{'═' * 41}{Colors.ENDC}")

def print_webmin_menu():
    """Print the Webmin submenu"""
    print_category("Webmin Management")
    print(f"{Colors.BLUE}1.{Colors.ENDC} Install Webmin")
    print(f"{Colors.BLUE}2.{Colors.ENDC} Uninstall Webmin")
    print(f"{Colors.BLUE}3.{Colors.ENDC} Start Webmin Service")
    print(f"{Colors.BLUE}4.{Colors.ENDC} Stop Webmin Service")
    print(f"{Colors.BLUE}5.{Colors.ENDC} Restart Webmin Service")
    print(f"{Colors.BLUE}6.{Colors.ENDC} Check Webmin Status")
    
    print(f"\n{Colors.RED}0.{Colors.ENDC} Back to Main Menu")
    print(f"{Colors.HEADER}{Colors.BOLD}{'═' * 49}{Colors.ENDC}")

def handle_webmin_menu():
    """Handle Webmin submenu choices"""
    while True:
        print_header()
        print_webmin_menu()
        choice = input(f"\n{Colors.BOLD}Enter your choice (0-6): {Colors.ENDC}")
        
        try:
            if choice == "1":
                install_webmin()
            elif choice == "2":
                uninstall_webmin()
            elif choice == "3":
                start_webmin_service()
            elif choice == "4":
                stop_webmin_service()
            elif choice == "5":
                restart_webmin_service()
            elif choice == "6":
                check_webmin_status()
            elif choice == "0":
                return
            else:
                print(f"\n{Colors.FAIL}❌ Invalid choice. Please try again.{Colors.ENDC}")
                wait_for_enter()
            
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ An error occurred: {str(e)}{Colors.ENDC}")
            input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")

def handle_choice(choice: str):
    """Handle main menu choices"""
    try:
        if choice == "1":
            handle_webmin_menu()
        elif choice == "2":
            # Handle other main menu option
            pass
        elif choice == "0":
            print(f"\n{Colors.GREEN}👋 Thank you for using TuxFetcher!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.FAIL}❌ Invalid choice. Please try again.{Colors.ENDC}")
            wait_for_enter()
        
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ An error occurred: {str(e)}{Colors.ENDC}")
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")


def main():
    """Main application loop"""
    check_admin_privileges()
    check_linux_os()
    while True:
        print_header()
        print_menu()
        choice = input(f"\n{Colors.BOLD}Enter your choice (0-4): {Colors.ENDC}")
        handle_choice(choice)


if __name__ == "__main__":
    main()
