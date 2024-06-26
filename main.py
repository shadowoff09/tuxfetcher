import os
import sys
from bind import install_bind, uninstall_bind
from webmin import uninstall_webmin, install_webmin
from sys import platform


# Function to display the menu
def display_menu():
    print("Select an option:")
    print("===============Bind DNS Server================")
    print("1. Install BIND DNS Server.")
    print("2. Uninstall BIND DNS Server.")
    print("================Webmin===============")
    print("3. Install Webmin.")
    print("4. Uninstall Webmin.")
    print("0. Exit")

    choice = input("Enter your choice: ").strip()
    if choice == "1":
        install_bind()
    elif choice == "2":
        uninstall_bind()
    elif choice == "3":
        install_webmin()
    elif choice == "4":
        uninstall_webmin()
    elif choice == "0":
        print("Exiting...")
        exit(0)
    else:
        print("Invalid choice. Please select a valid option.")
        display_menu()


if __name__ == "__main__":
    # Check if the script is running on a linux based system
    if not platform.startswith('linux'):
        print("This script must be run in a linux based system.")
        sys.exit(1)
    # Check if the script is being run with sudo privileges
    elif os.geteuid() != 0:
        print("This script must be run with sudo privileges.")
        sys.exit(1)

    display_menu()
