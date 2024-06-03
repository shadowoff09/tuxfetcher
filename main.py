import os
import sys
from bind import install_bind, is_dns_server_running, revert_changes


# Function to display the menu
def display_menu():
    print("Select an option:")
    print("1. Install BIND DNS Server")
    print("2. Revert Changes (Uninstall BIND DNS Server)")
    print("0. Exit")

    choice = input("Enter your choice: ").strip()
    if choice == "1":
        install_bind()
    elif choice == "2":
        if is_dns_server_running():
            print("Error: DNS server is still running. Please stop the DNS server before reverting changes.")
        else:
            revert_changes()
            print("BIND DNS server changes reverted successfully.")
    elif choice == "0":
        print("Exiting...")
        exit(0)
    else:
        print("Invalid choice. Please select a valid option.")
        display_menu()


if __name__ == "__main__":
    # Check if the script is being run with sudo privileges
    if os.geteuid() != 0:
        print("This script must be run with sudo privileges.")
        sys.exit(1)

    display_menu()
