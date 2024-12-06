import os
import sys
import time
import subprocess
import itertools
import threading
from tqdm import tqdm
from common import get_input, update_system


class Spinner:
    """A class to manage the spinner animation"""
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """Start the spinner"""
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the spinner"""
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the spinner character
        sys.stdout.write('\b \b')
        sys.stdout.flush()

    def _animate(self):
        """Animate the spinner"""
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        while self.running:
            sys.stdout.write(next(spinner))
            sys.stdout.flush()
            sys.stdout.write('\b')
            time.sleep(0.1)


def run_command_with_progress(command: list, description: str, time_estimate: int = 3, show_output: bool = False):
    """Run a command with a progress bar and spinner"""
    spinner = Spinner()
    
    with tqdm(total=100, 
             desc=f"{description}", 
             bar_format='{desc:<30} |{bar:30}| {percentage:3.0f}% {postfix}',
             unit='%') as pbar:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start the spinner
        spinner.start()
        
        try:
            # Simulate progress while command is running
            progress = 0
            increment = 100 / (time_estimate * 4)  # Update 4 times per second
            
            while process.poll() is None and progress < 95:
                # Read output without blocking
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()
                
                if show_output:
                    if stdout_line:
                        tqdm.write(f"Output: {stdout_line.strip()}")
                    if stderr_line:
                        tqdm.write(f"Error: {stderr_line.strip()}")
                
                time.sleep(0.25)
                progress += increment
                pbar.update(min(increment, 95 - pbar.n))
                pbar.set_postfix_str("⋯")
            
            # Get remaining output
            stdout, stderr = process.communicate()
            if show_output and (stdout or stderr):
                tqdm.write(f"Final output: {stdout}\nErrors: {stderr}")
            
            # Complete the progress bar
            if process.returncode == 0:
                pbar.update(100 - pbar.n)
                pbar.set_postfix_str("✓")
            else:
                error_msg = stderr.strip() if stderr else "Unknown error"
                raise subprocess.CalledProcessError(process.returncode, command, stderr=error_msg)
            
            return process.returncode
            
        finally:
            # Always stop the spinner
            spinner.stop()


def get_user_output_preference():
    """Ask user if they want to see command output"""
    while True:
        choice = input("\nDo you want to see detailed command output? (y/n): ").lower().strip()
        if choice in ['y', 'n']:
            return choice == 'y'
        print("Please enter 'y' for yes or 'n' for no.")


def install_bind_packages(show_output: bool = False):
    """Install BIND packages with progress bar"""
    run_command_with_progress(
        ["sudo", "apt-get", "install", "-y", "bind9", "bind9utils", "bind9-doc"],
        "Installing BIND packages",
        20,
        show_output
    )


def configure_named_conf_options(FORWARDER_CONFIG):
    """Configure named.conf.options file"""
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
    """Configure named.conf.local file"""
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
    """Create zone files for forward and reverse DNS"""
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


def set_zone_file_permissions(show_output: bool = False):
    """Set proper permissions for zone files"""
    run_command_with_progress(
        ["sudo", "chown", "-R", "bind:bind", "/etc/bind/zones"],
        "Setting zone file permissions",
        2,
        show_output
    )
    run_command_with_progress(
        ["sudo", "chmod", "-R", "755", "/etc/bind/zones"],
        "Setting zone file permissions",
        2,
        show_output
    )


def check_bind_configuration(DOMAIN, REVERSE_DOMAIN, forward_zone_path, reverse_zone_path, show_output: bool = False):
    """Check BIND configuration files for syntax errors"""
    run_command_with_progress(
        ["sudo", "named-checkconf"],
        "Checking BIND configuration",
        2,
        show_output
    )
    run_command_with_progress(
        ["sudo", "named-checkzone", DOMAIN, forward_zone_path],
        "Checking forward zone",
        2,
        show_output
    )
    run_command_with_progress(
        ["sudo", "named-checkzone", REVERSE_DOMAIN, reverse_zone_path],
        "Checking reverse zone",
        2,
        show_output
    )


def restart_bind_service(show_output: bool = False):
    """Restart and enable BIND service"""
    run_command_with_progress(
        ["sudo", "service", "bind9", "restart"],
        "Restarting BIND service",
        3,
        show_output
    )
    run_command_with_progress(
        ["sudo", "systemctl", "restart", "named"],
        "Restarting named service",
        3,
        show_output
    )
    run_command_with_progress(
        ["sudo", "systemctl", "enable", "named"],
        "Enabling BIND service",
        2,
        show_output
    )


def is_bind_installed():
    """Check if BIND is installed"""
    try:
        result = subprocess.run(["dpkg", "-l", "bind9"], capture_output=True, text=True)
        return "ii  bind9" in result.stdout
    except subprocess.CalledProcessError:
        return False


def configure_system_dns(dns_ip: str, show_output: bool = False) -> bool:
    """Configure system to use the new DNS server"""
    try:
        # Backup current resolv.conf
        if os.path.exists("/etc/resolv.conf"):
            run_command_with_progress(
                ["sudo", "cp", "/etc/resolv.conf", "/etc/resolv.conf.backup"],
                "Backing up DNS configuration",
                1,
                show_output
            )
        
        # Update resolv.conf
        with open("/tmp/resolv.conf", "w") as f:
            f.write(f"nameserver {dns_ip}\n")
        
        run_command_with_progress(
            ["sudo", "mv", "/tmp/resolv.conf", "/etc/resolv.conf"],
            "Updating DNS configuration",
            1,
            show_output
        )
        
        return True
    except Exception as e:
        print(f"❌ Failed to configure system DNS: {str(e)}")
        return False


def test_dns_installation(domain: str, dns_ip: str, show_output: bool = False) -> bool:
    """Run a series of tests to verify DNS installation"""
    print("\n🔍 Testing DNS Installation:")
    all_tests_passed = True
    
    try:
        # Test 1: Check if BIND is running
        print("\n📋 Test 1: Checking BIND service status")
        result = subprocess.run(
            ["systemctl", "is-active", "bind9"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip() == "active":
            print("✅ BIND service is running")
        else:
            print("❌ BIND service is not running")
            all_tests_passed = False
        
        # Test 2: Test DNS resolution using nslookup
        print("\n📋 Test 2: Testing domain resolution with nslookup")
        result = subprocess.run(
            ["nslookup", domain, dns_ip],
            capture_output=True,
            text=True
        )
        if "server can't find" not in result.stderr and dns_ip in result.stdout:
            print("✅ Domain resolution successful")
            if show_output:
                print(f"Output:\n{result.stdout}")
        else:
            print("❌ Domain resolution failed")
            if show_output:
                print(f"Error:\n{result.stderr}")
            all_tests_passed = False
        
        # Test 3: Test DNS resolution using dig
        print("\n📋 Test 3: Testing domain resolution with dig")
        result = subprocess.run(
            ["dig", f"@{dns_ip}", domain],
            capture_output=True,
            text=True
        )
        if "ANSWER: 0" not in result.stdout and "status: NOERROR" in result.stdout:
            print("✅ Dig query successful")
            if show_output:
                print(f"Output:\n{result.stdout}")
        else:
            print("❌ Dig query failed")
            if show_output:
                print(f"Error:\n{result.stderr}")
            all_tests_passed = False
        
        # Test 4: Check zone file permissions
        print("\n📋 Test 4: Checking zone file permissions")
        result = subprocess.run(
            ["ls", "-l", "/etc/bind/zones"],
            capture_output=True,
            text=True
        )
        if "bind bind" in result.stdout:
            print("✅ Zone file permissions are correct")
        else:
            print("❌ Zone file permissions are incorrect")
            all_tests_passed = False
        
        # Test 5: Check configuration syntax
        print("\n📋 Test 5: Verifying configuration syntax")
        result = subprocess.run(
            ["named-checkconf"],
            capture_output=True,
            text=True
        )
        if not result.stderr:
            print("✅ Configuration syntax is valid")
        else:
            print("❌ Configuration syntax has errors")
            if show_output:
                print(f"Error:\n{result.stderr}")
            all_tests_passed = False
        
        return all_tests_passed
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False


def show_dns_instructions(DOMAIN: str, DNS_SERVER_IP: str, tests_passed: bool):
    """Show DNS configuration instructions"""
    print("\n🔧 DNS Server Configuration:")
    print(f"   Primary Domain: {DOMAIN}")
    print(f"   DNS Server IP: {DNS_SERVER_IP}")
    
    print("\n📝 Created Files:")
    print("   - /etc/bind/zones/")
    print(f"   - /etc/bind/zones/db.{DOMAIN}")
    print("   - /etc/bind/named.conf.options")
    print("   - /etc/bind/named.conf.local")
    
    if not tests_passed:
        print("\n⚠️  Some tests failed. Troubleshooting steps:")
        print("   1. Check BIND logs:")
        print("      $ sudo journalctl -u bind9")
        print("   2. Verify configuration files:")
        print("      $ sudo named-checkconf")
        print("      $ sudo named-checkzone")
        print("   3. Check file permissions:")
        print("      $ ls -l /etc/bind/zones")
        print("   4. Restart BIND service:")
        print("      $ sudo systemctl restart bind9")
    
    print("\n💡 Next Steps:")
    print("   1. Configure your clients to use this DNS server")
    print(f"   2. Add the DNS server IP ({DNS_SERVER_IP}) to your network settings")
    print("   3. Test the DNS resolution with:")
    print(f"      $ nslookup {DOMAIN} {DNS_SERVER_IP}")
    print(f"      $ dig @{DNS_SERVER_IP} {DOMAIN}")
    
    print("\n⚠️  Note: DNS changes may take some time to propagate")
    print("   If you experience issues, check the logs with:")
    print("   $ sudo journalctl -u bind9")


def get_system_hostname():
    """Get the current system's hostname"""
    try:
        hostname = subprocess.run(["hostname", "-f"], 
                                capture_output=True, 
                                text=True).stdout.strip()
        return hostname
    except:
        return None


def get_system_ip():
    """Get the current system's IP address"""
    try:
        # Try to get IP from hostname
        ip = subprocess.run(["hostname", "-I"], 
                          capture_output=True, 
                          text=True).stdout.strip().split()[0]
        return ip
    except:
        return None


def validate_domain(domain: str) -> tuple[bool, str]:
    """Validate domain name and check for common TLD conflicts"""
    common_tlds = ['.com', '.net', '.org', '.edu', '.gov', '.mil', '.int', 
                  '.local', '.test', '.example', '.invalid', '.localhost']
    
    # Basic domain validation
    if not domain:
        return False, "Domain cannot be empty"
    if len(domain) > 253:
        return False, "Domain name too long (max 253 characters)"
    if not all(c.isalnum() or c in '.-' for c in domain):
        return False, "Domain can only contain letters, numbers, dots, and hyphens"
    if domain.startswith('.') or domain.endswith('.'):
        return False, "Domain cannot start or end with a dot"
    if '..' in domain:
        return False, "Domain cannot contain consecutive dots"
    
    # Check for TLD conflicts
    domain_lower = domain.lower()
    for tld in common_tlds:
        if domain_lower.endswith(tld):
            return False, f"Warning: Using {tld} TLD might conflict with existing domains"
    
    return True, "Domain is valid"


def get_reverse_domain(ip: str) -> str:
    """Generate reverse domain from IP address"""
    try:
        # Split IP into octets and reverse them
        octets = ip.split('.')
        if len(octets) != 4:
            return None
        return f"{octets[2]}.{octets[1]}.{octets[0]}.in-addr.arpa"
    except:
        return None


def suggest_local_domains(hostname: str = None) -> list[str]:
    """Generate suggested local domain names"""
    suggestions = [
        "home.lan",
        "local.net",
        "internal.network",
        "home.network",
        "private.lan",
        "lab.local",
        "home.arpa",  # RFC 8375 recommended
    ]
    
    if hostname:
        # Add some suggestions based on hostname if available
        hostname_base = hostname.split('.')[0]
        suggestions.extend([
            f"{hostname_base}.home.arpa",
            f"{hostname_base}.local",
            f"{hostname_base}.lan"
        ])
    
    return suggestions


def get_domain_input() -> tuple[str, str, str]:
    """Get domain, reverse domain and DNS server IP with validation"""
    print("\n🌐 Domain Configuration:")
    
    # Get system information
    system_hostname = get_system_hostname()
    system_ip = get_system_ip()
    
    if system_hostname and system_ip:
        print(f"\nℹ️  Current system details:")
        print(f"   Hostname: {system_hostname}")
        print(f"   IP Address: {system_ip}")
    
    # Show domain suggestions
    print("\n📝 Suggested Local Domains:")
    suggestions = suggest_local_domains(system_hostname)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    print("\n💡 Domain Name Guidelines:")
    print("   - Use only letters, numbers, dots, and hyphens")
    print("   - Avoid using common TLDs (.com, .net, etc.)")
    print("   - Consider using .local, .lan, or .home.arpa")
    print("   - You can enter a number to use a suggestion or type your own domain")
    
    # Get domain with validation
    while True:
        domain_input = input("\nEnter your domain (or number for suggestion): ").strip()
        
        # Check if user entered a suggestion number
        if domain_input.isdigit():
            num = int(domain_input)
            if 1 <= num <= len(suggestions):
                domain = suggestions[num-1]
            else:
                print("❌ Invalid suggestion number")
                continue
        else:
            domain = domain_input
        
        # Validate the domain
        is_valid, message = validate_domain(domain)
        if is_valid:
            print(f"✅ {message}")
            break
        else:
            print(f"❌ {message}")
            retry = input("Do you want to try again? (y/n): ").lower().strip()
            if retry != 'y':
                raise Exception("Domain configuration cancelled by user")
    
    # Get DNS server IP
    while True:
        use_current_ip = input(f"\nDo you want to use this computer's IP ({system_ip}) as the DNS server? (y/n): ").lower().strip() if system_ip else 'n'
        
        if use_current_ip == 'y':
            dns_ip = system_ip
            break
        else:
            dns_ip = input("Enter your DNS server IP address: ").strip()
            # Basic IP validation
            octets = dns_ip.split('.')
            if len(octets) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
                break
            print("❌ Invalid IP address format. Use format: xxx.xxx.xxx.xxx")
    
    # Generate reverse domain
    reverse_domain = get_reverse_domain(dns_ip)
    if not reverse_domain:
        while True:
            print("\n📝 Reverse Domain Guidelines:")
            print("   - Format: x.x.x.in-addr.arpa")
            print("   - Based on the first three octets of your IP in reverse")
            print(f"   Example: For IP {dns_ip}, use: {'.'.join(dns_ip.split('.')[:3][::-1])}.in-addr.arpa")
            
            reverse_domain = input("\nEnter your reverse domain: ").strip()
            if reverse_domain.endswith('.in-addr.arpa'):
                break
            print("❌ Invalid reverse domain format")
    
    print("\n✅ Domain Configuration Summary:")
    print(f"   Domain: {domain}")
    print(f"   Reverse Domain: {reverse_domain}")
    print(f"   DNS Server IP: {dns_ip}")
    
    confirm = input("\nConfirm these settings? (y/n): ").lower().strip()
    if confirm != 'y':
        raise Exception("Domain configuration cancelled by user")
    
    return domain, reverse_domain, dns_ip


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system"""
    try:
        subprocess.run(["which", command], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def install_required_packages(show_output: bool = False) -> bool:
    """Install required system packages"""
    required_packages = {
        'dnsutils': ['nslookup', 'dig'],
        'bind9': ['named'],
        'bind9utils': ['named-checkconf'],
    }
    
    missing_packages = []
    
    # Check which packages need to be installed
    for package, commands in required_packages.items():
        for cmd in commands:
            if not check_command_exists(cmd):
                if package not in missing_packages:
                    missing_packages.append(package)
                break
    
    if missing_packages:
        print(f"\n⚠️  Missing required packages: {', '.join(missing_packages)}")
        print("ℹ️  These packages are needed for DNS server functionality")
        
        install = input("\nDo you want to install these packages? (y/n): ").lower().strip()
        if install != 'y':
            return False
        
        try:
            # Update package list
            print("\n🔄 Updating package list...")
            run_command_with_progress(
                ["sudo", "apt-get", "update"],
                "Updating package list",
                5,
                show_output
            )
            
            # Install missing packages
            print("\n📥 Installing required packages...")
            run_command_with_progress(
                ["sudo", "apt-get", "install", "-y"] + missing_packages,
                "Installing packages",
                20,
                show_output
            )
            
            print("\n✅ All required packages installed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Failed to install packages: {str(e)}")
            return False
    
    return True


def check_and_install_dependencies(show_output: bool = False) -> bool:
    """Check and install required system packages"""
    try:
        # Check for dnsutils (contains nslookup and dig)
        result = subprocess.run(
            ["which", "nslookup"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("\n⚠️  Required package 'dnsutils' is not installed")
            print("ℹ️  This package provides nslookup and dig commands needed for DNS testing")
            
            install = input("\nDo you want to install it? (y/n): ").lower().strip()
            if install != 'y':
                return False
            
            # Install dnsutils
            print("\n📥 Installing dnsutils package...")
            run_command_with_progress(
                ["sudo", "apt-get", "update"],
                "Updating package list",
                5,
                show_output
            )
            run_command_with_progress(
                ["sudo", "apt-get", "install", "-y", "dnsutils"],
                "Installing dnsutils",
                10,
                show_output
            )
            
            print("✅ dnsutils installed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking dependencies: {str(e)}")
        return False


def install_bind():
    """Install and configure BIND DNS Server with progress bars"""
    try:
        print("\n📦 Installing BIND DNS Server...")
        print("⚠️  Note: This script is not intended for production environments, only for development and testing purposes.\n")
        
        # Ask user about output visibility
        show_output = get_user_output_preference()
        if show_output:
            print("\n⚠️  Detailed command output will be shown.")
        else:
            print("\n⚠️  Only progress bars will be shown.")
        
        # Check and install dependencies first
        if not check_and_install_dependencies(show_output):
            raise Exception("Required packages could not be installed")
        
        # Get domain configuration
        DOMAIN, REVERSE_DOMAIN, DNS_SERVER_IP = get_domain_input()
        
        # Ask if user wants to configure system DNS
        configure_dns = input("\nDo you want to configure this computer to use the new DNS server? (y/n): ").lower().strip() == 'y'
        
        # Get admin email
        ADMIN_EMAIL = get_input(
            "Enter the admin email (replace @ with .) (e.g., admin.example.com)", 
            f"admin.{DOMAIN}"
        )
        
        # Get forwarders
        print("\n📝 DNS Forwarders:")
        print("   These are the upstream DNS servers to use when a record is not found")
        print("   Common options:")
        print("   - Google DNS: 8.8.8.8, 8.8.4.4")
        print("   - Cloudflare: 1.1.1.1, 1.0.0.1")
        print("   - OpenDNS: 208.67.222.222, 208.67.220.220")
        
        FORWARDERS = get_input(
            "Enter the DNS forwarder IP addresses (comma-separated)",
            "8.8.8.8,8.8.4.4"
        )
        
        # Format forwarders
        FORWARDER_ARRAY = FORWARDERS.split(',')
        FORWARDER_CONFIG = "\n".join(f"{fw};" for fw in FORWARDER_ARRAY)
        
        # Update system
        print("\n🔄 Updating system packages...")
        run_command_with_progress(
            ["sudo", "apt-get", "update"],
            "Updating package list",
            5,
            show_output
        )
        
        # Install BIND
        print("\n📥 Installing BIND packages...")
        install_bind_packages(show_output)
        
        # Configure BIND
        print("\n⚙️  Configuring BIND...")
        configure_named_conf_options(FORWARDER_CONFIG)
        configure_named_conf_local(DOMAIN, REVERSE_DOMAIN)
        
        # Create and configure zones
        print("\n📝 Creating zone files...")
        forward_zone_path, reverse_zone_path = create_zone_files(
            DOMAIN, REVERSE_DOMAIN, DNS_SERVER_IP, ADMIN_EMAIL
        )
        
        # Set permissions
        print("\n🔒 Setting permissions...")
        set_zone_file_permissions(show_output)
        
        # Check configuration
        print("\n✅ Validating configuration...")
        check_bind_configuration(DOMAIN, REVERSE_DOMAIN, forward_zone_path, reverse_zone_path, show_output)
        
        # Start service
        print("\n🚀 Starting BIND service...")
        restart_bind_service(show_output)
        
        # Test the installation
        print("\n🔍 Running DNS server tests...")
        tests_passed = test_dns_installation(DOMAIN, DNS_SERVER_IP, show_output)
        
        # Configure system DNS if requested
        if configure_dns:
            print("\n⚙️  Configuring system DNS...")
            if configure_system_dns(DNS_SERVER_IP, show_output):
                print("✅ System DNS configured successfully")
            else:
                print("❌ Failed to configure system DNS")
        
        print("\n✅ BIND DNS server setup completed!")
        show_dns_instructions(DOMAIN, DNS_SERVER_IP, tests_passed)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during installation: {e.stderr}")
        raise
    except Exception as e:
        print(f"\n❌ Error during installation: {str(e)}")
        raise


def uninstall_bind():
    """Uninstall BIND DNS Server and all its components"""
    if not is_bind_installed():
        print("\n⚠️ BIND DNS Server is not installed.")
        return

    try:
        print("\n🗑️  Uninstalling BIND DNS Server...")
        
        # Ask user about output visibility
        show_output = get_user_output_preference()
        if show_output:
            print("\n⚠️  Detailed command output will be shown.")
        else:
            print("\n⚠️  Only progress bars will be shown.")
        
        # Backup DNS configuration if exists
        if os.path.exists("/etc/resolv.conf"):
            print("\n💾 Backing up current DNS configuration...")
            run_command_with_progress(
                ["sudo", "cp", "/etc/resolv.conf", "/etc/resolv.conf.backup"],
                "Creating backup",
                1,
                show_output
            )
        
        # Stop BIND services
        print("\n🛑 Stopping BIND services...")
        run_command_with_progress(
            ["sudo", "systemctl", "stop", "bind9"],
            "Stopping bind9 service",
            2,
            show_output
        )
        run_command_with_progress(
            ["sudo", "systemctl", "stop", "named"],
            "Stopping named service",
            2,
            show_output
        )
        
        # Disable services
        print("\n⚡ Disabling BIND services...")
        run_command_with_progress(
            ["sudo", "systemctl", "disable", "bind9"],
            "Disabling bind9 service",
            2,
            show_output
        )
        run_command_with_progress(
            ["sudo", "systemctl", "disable", "named"],
            "Disabling named service",
            2,
            show_output
        )

        # Remove all installed packages
        print("\n🗑️  Removing packages...")
        packages_to_remove = [
            "bind9",
            "bind9utils",
            "bind9-doc",
            "dnsutils"  # Added by our dependency check
        ]
        
        run_command_with_progress(
            ["sudo", "apt-get", "remove", "--purge", "-y"] + packages_to_remove,
            "Removing BIND packages",
            10,
            show_output
        )
        
        # Remove dependencies
        run_command_with_progress(
            ["sudo", "apt-get", "autoremove", "-y"],
            "Removing dependencies",
            5,
            show_output
        )

        # Remove configuration files and directories
        print("\n🧹 Cleaning up configuration files...")
        directories_to_remove = [
            "/etc/bind",
            "/var/cache/bind",
            "/var/lib/bind"
        ]
        
        for directory in directories_to_remove:
            if os.path.exists(directory):
                run_command_with_progress(
                    ["sudo", "rm", "-rf", directory],
                    f"Removing {directory}",
                    2,
                    show_output
                )
        
        # Restore original resolv.conf if backup exists
        if os.path.exists("/etc/resolv.conf.backup"):
            print("\n🔄 Restoring original DNS configuration...")
            run_command_with_progress(
                ["sudo", "mv", "/etc/resolv.conf.backup", "/etc/resolv.conf"],
                "Restoring DNS configuration",
                1,
                show_output
            )
        
        # Clean package cache
        run_command_with_progress(
            ["sudo", "apt-get", "clean"],
            "Cleaning package cache",
            2,
            show_output
        )
        
        # Update package list
        run_command_with_progress(
            ["sudo", "apt-get", "update"],
            "Updating package list",
            5,
            show_output
        )

        print("\n✅ BIND DNS Server has been completely uninstalled!")
        print("\nℹ️  Summary of removed components:")
        print("   - BIND DNS Server and utilities")
        print("   - DNS utilities (nslookup, dig)")
        print("   - Configuration files and zones")
        print("   - System services and cache")
        if os.path.exists("/etc/resolv.conf"):
            print("   - Restored original DNS configuration")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during uninstallation: {e.stderr}")
        raise
    except Exception as e:
        print(f"\n❌ Error during uninstallation: {str(e)}")
        raise
