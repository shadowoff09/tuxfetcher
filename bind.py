import os
import subprocess

from common import get_input, update_system


def install_bind_packages():
    print("Installing BIND packages...")
    subprocess.run(["sudo", "apt-get", "install", "-y", "bind9", "bind9utils", "bind9-doc"])


def configure_named_conf_options(FORWARDER_CONFIG):
    named_conf_options = f"""
options {{
    directory "/var/cache/bind";

    recursion yes;
    allow-recursion {{ any; }};
    listen-on {{ any; }};
    allow-transfer {{ none; }};

    forwarders {{
        {FORWARDER_CONFIG}
    }};

    auth-nxdomain no;    # conform to RFC1035
    listen-on-v6 {{ any; }};
}};
"""
    with open("/etc/bind/named.conf.options", "w") as f:
        f.write(named_conf_options)


def configure_named_conf_local(DOMAIN, REVERSE_DOMAIN):
    named_conf_local = f"""
zone "{DOMAIN}" {{
    type master;
    file "/etc/bind/zones/db.{DOMAIN}";
}};

zone "{REVERSE_DOMAIN}" {{
    type master;
    file "/etc/bind/zones/db.{REVERSE_DOMAIN}";
}};
"""
    with open("/etc/bind/named.conf.local", "w") as f:
        f.write(named_conf_local)


def create_zone_files(DOMAIN, REVERSE_DOMAIN, DNS_SERVER_IP, ADMIN_EMAIL):
    # Create the zones directory if it doesn't exist
    os.makedirs("/etc/bind/zones", exist_ok=True)

    forward_zone_file = f"""
;
; BIND data file for {DOMAIN}
;
$TTL    604800
@       IN      SOA     ns1.{DOMAIN}. {ADMIN_EMAIL}. (
                             {os.popen('date +%Y%m%d01').read().strip()}   ; Serial
                             604800              ; Refresh
                             86400               ; Retry
                             2419200             ; Expire
                             604800 )            ; Negative Cache TTL
;
@       IN      NS      ns1.{DOMAIN}.
@       IN      A       {DNS_SERVER_IP}
ns1     IN      A       {DNS_SERVER_IP}
www     IN      A       {DNS_SERVER_IP}
"""
    forward_zone_path = f"/etc/bind/zones/db.{DOMAIN}"
    with open(forward_zone_path, "w") as f:
        f.write(forward_zone_file)

    reverse_zone_file = f"""
;
; BIND reverse data file for {REVERSE_DOMAIN}
;
$TTL    604800
@       IN      SOA     ns1.{DOMAIN}. {ADMIN_EMAIL}. (
                             {os.popen('date +%Y%m%d01').read().strip()}   ; Serial
                             604800              ; Refresh
                             86400               ; Retry
                             2419200             ; Expire
                             604800 )            ; Negative Cache TTL
;
@       IN      NS      ns1.{DOMAIN}.
10      IN      PTR     {DOMAIN}.
"""
    reverse_zone_path = f"/etc/bind/zones/db.{REVERSE_DOMAIN}"
    with open(reverse_zone_path, "w") as f:
        f.write(reverse_zone_file)

    return forward_zone_path, reverse_zone_path


def set_zone_file_permissions():
    # Set the owner and permissions for the zones directory
    subprocess.run(["sudo", "chown", "-R", "bind:bind", "/etc/bind/zones"])
    subprocess.run(["sudo", "chmod", "-R", "755", "/etc/bind/zones"])


def check_bind_configuration(DOMAIN, REVERSE_DOMAIN, forward_zone_path, reverse_zone_path):
    # Check the BIND configuration files for syntax errors
    subprocess.run(["sudo", "named-checkconf"])
    subprocess.run(["sudo", "named-checkzone", DOMAIN, forward_zone_path])
    subprocess.run(["sudo", "named-checkzone", REVERSE_DOMAIN, reverse_zone_path])


def restart_bind_service():
    # Restart the BIND service and enable it to start on boot
    subprocess.run(["sudo", "service", "bind9", "restart"])
    subprocess.run(["sudo", "systemctl", "restart", "named"])
    subprocess.run(["sudo", "systemctl", "enable", "named"])

def install_bind():
    print("Welcome to the BIND DNS Server Installation Script!")
    print(
        "WARNING: This script is not intended for production environments, only for development and testing purposes.\n")

    # Determine default values
    default_forwarders = "8.8.8.8,8.8.4.4"

    # Prompt the user for input with default values
    DOMAIN = input("Enter your domain (e.g., example.com)")
    REVERSE_DOMAIN = input("Enter your reverse domain (e.g., 1.168.192.in-addr.arpa)")
    DNS_SERVER_IP = input("Enter your DNS server IP address")
    ADMIN_EMAIL = get_input("Enter the admin email (replace @ with .) (e.g., admin.example.com)", f"admin.{DOMAIN}")
    FORWARDERS = get_input("Enter the DNS forwarder IP addresses (comma-separated, e.g., 8.8.8.8,8.8.4.4)", default_forwarders)

    # Split the forwarders string into an array and create the forwarder configuration
    FORWARDER_ARRAY = FORWARDERS.split(',')
    FORWARDER_CONFIG = "\n".join(f"{fw};" for fw in FORWARDER_ARRAY)

    # Update packages
    update_system()

    # Install BIND packages
    install_bind_packages()

    # Configure named.conf.options
    configure_named_conf_options(FORWARDER_CONFIG)

    # Configure named.conf.local
    configure_named_conf_local(DOMAIN, REVERSE_DOMAIN)

    # Create zone files
    forward_zone_path, reverse_zone_path = create_zone_files(DOMAIN, REVERSE_DOMAIN, DNS_SERVER_IP, ADMIN_EMAIL)

    # Set permissions
    set_zone_file_permissions()

    # Check configuration
    check_bind_configuration(DOMAIN, REVERSE_DOMAIN, forward_zone_path, reverse_zone_path)

    # Restart BIND service
    restart_bind_service()

    print("BIND DNS server setup completed successfully.")
    print("\nThe following files and directories were created:")
    print(f"Zones directory: /etc/bind/zones")
    print(f"Forward zone file: {forward_zone_path}")
    print(f"Reverse zone file: {reverse_zone_path}")
    print("/etc/bind/named.conf.options")
    print("/etc/bind/named.conf.local")


# Function to check if the DNS server is running
def is_dns_server_running():
    dns_running = False
    try:
        result = subprocess.run(["sudo", "service", "bind9", "status"], capture_output=True, text=True)
        if "Active: active" in result.stdout:
            dns_running = True
    except subprocess.CalledProcessError:
        pass
    return dns_running


def uninstall_bind():
    if is_dns_server_running():
        user_wants_to_uninstall = input("The Bind DNS Server is currently running, are you sure you want to uninstall it? (y/n): ").lower()
        if user_wants_to_uninstall == "y":
            # Stop BIND service
            subprocess.run(["sudo", "service", "bind9", "stop"])
            subprocess.run(["sudo", "service", "named", "stop"])

            # Remove BIND packages
            subprocess.run(["sudo", "apt", "remove", "--purge", "-y", "bind9", "bind9utils", "bind9-doc"])

            # Remove BIND configuration files and directories
            subprocess.run(["sudo", "rm", "-rf", "/etc/bind"])
        elif user_wants_to_uninstall == "n":
            print("Uninstallation cancelled.")
        else:
            print("Invalid choice. Please enter 'y' or 'n'.")
