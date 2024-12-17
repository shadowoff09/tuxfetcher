import subprocess
import os
import getpass
import crypt
from common.colors import Colors
from common.utils import update_system, update_system, run_command, update_repositories, wait_for_enter


def get_root_password():
    """Get the root user password"""
    try:
        with open('/etc/shadow', 'r') as f:
            for line in f:
                if line.startswith('root:'):
                    return True if line.split(':')[1] not in ['*', '!', ''] else False
    except:
        return False


def setup_webmin_repository():
    """Set up Webmin repository manually without using the setup script"""
    try:
        # Add Webmin GPG key
        print("\n🔑 Adding Webmin GPG key...")
        run_command(["sudo", "curl", "-fsSL", "http://www.webmin.com/jcameron-key.asc", "-o", "/usr/share/keyrings/webmin-keyring.asc"])

        # Add Webmin repository to sources list
        print("\n📝 Adding Webmin repository to sources list...")
        repo_line = "deb [signed-by=/usr/share/keyrings/webmin-keyring.asc] http://download.webmin.com/download/repository sarge contrib"
        with open("/tmp/webmin.list", "w") as f:
            f.write(repo_line)
        
        run_command(["sudo", "mv", "/tmp/webmin.list", "/etc/apt/sources.list.d/webmin.list"])

        # Update package list
        print("\n🔄 Updating package list...")
        update_repositories()

        return True
    except Exception as e:
        print(f"\n❌ Error setting up Webmin repository: {str(e)}")
        return False


def create_webmin_user():
    """Create a dedicated user for Webmin"""
    username = "webmin"
    password = "webmin"

    try:
        # Create system user if doesn't exist
        encrypted_pass = crypt.crypt(password)
        print("\n📝 Creating user account...")
        
        # Try to create user, ignore if exists
        run_command(
            ["sudo", "useradd", "-m", "-s", "/bin/bash", "-p", encrypted_pass, username],
            check=False
        )
        
        print(f"\n{Colors.GREEN}✅ User account created successfully.{Colors.ENDC}")

        # Add user to sudo group for Webmin access
        print("\n📝 Adding user to sudo group...")
        run_command(
            ["sudo", "usermod", "-aG", "sudo", username],
            check=False
        )
        print(f"\n{Colors.GREEN}✅ User added to sudo group successfully.{Colors.ENDC}")

        return username, password
    except Exception as e:
        # Continue silently if there are any errors
        return username, password


def show_login_instructions(webmin_user=None, webmin_pass=None):
    """Show Webmin login instructions"""
    print("\n🔐 Login Information:")
    print("   URL: https://localhost:10000")
    
    if webmin_user and webmin_pass:
        print(f"   Username: {webmin_user}")
        print(f"   Password: {webmin_pass}")
        print("\n💡 Note: Please save these credentials securely!")
    else:
        # Check if root password is set
        if get_root_password():
            print("   Username: root")
            print("   Password: Your system's root password")
        else:
            print("   Username: Your system username")
            print("   Password: Your system user password")
    
    print("\n⚠️  Note: Webmin uses HTTPS, so you might see a security warning in your browser.")
    print("   This is normal for a local installation. You can safely proceed.")
    print("\n💡 Tips:")
    print("   - If you can't access Webmin, make sure port 10000 is not blocked by your firewall")
    print("   - First-time login might take a few moments as Webmin initializes")
    print("   - For security, change your password after first login")


def install_webmin():
    """Install Webmin"""
    if is_webmin_installed():
        print(f"\n{Colors.RED}❌ Webmin is already installed.{Colors.ENDC}")
        wait_for_enter()
        return
    
    try:
        print("\n📦 Installing Webmin...")
        
        # Update system
        update_system()
        
        # Set up Webmin repository
        print(f"\n{Colors.BLUE}⚙️  Setting up Webmin repository...{Colors.ENDC}")
        if not setup_webmin_repository():
            raise Exception("Failed to set up Webmin repository")
        print(f"\n{Colors.GREEN}✅ Webmin repository set up successfully.{Colors.ENDC}")
        
        
        # Install Webmin with output display
        print(f"\n{Colors.BLUE}📥 Installing Webmin packages...{Colors.ENDC}")        
        run_command(["sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", "webmin", "--install-recommends"])
        print(f"\n{Colors.GREEN}✅ Webmin packages installed successfully.{Colors.ENDC}")
        
        # Create Webmin user if requested
        webmin_user, webmin_pass = create_webmin_user()
        
        print(f"\n{Colors.GREEN}✅ Webmin installation completed successfully!{Colors.ENDC}")
        show_login_instructions(webmin_user, webmin_pass)
        wait_for_enter()
        
        
    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.RED}❌ Error during installation: {e.stderr}{Colors.ENDC}")
        raise
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error during installation: {str(e)}{Colors.ENDC}")
        raise

def stop_webmin_service():
    """Stop the Webmin service"""
    if not is_webmin_installed():
        print(f"\n{Colors.RED}❌ Webmin is not installed.{Colors.ENDC}")
        wait_for_enter()
        return
    
    if not is_webmin_running():
        print(f"\n{Colors.RED}❌ Webmin is not running.{Colors.ENDC}")
        wait_for_enter()
        return
    
    try:
        run_command(["sudo", "systemctl", "stop", "webmin"])
        print(f"\n{Colors.GREEN}✅ Webmin service stopped successfully.{Colors.ENDC}")
        wait_for_enter()
        return True
    except subprocess.CalledProcessError:
        print("⚠️ Warning: Could not stop Webmin service. Continuing with uninstallation...")
        return False
    
def start_webmin_service():
    """Start the Webmin service"""
    if not is_webmin_installed():
        print(f"\n{Colors.RED}❌ Webmin is not installed.{Colors.ENDC}")
        wait_for_enter()
        return
    
    if is_webmin_running():
        print(f"\n{Colors.RED}❌ Webmin service is already running.{Colors.ENDC}")
        wait_for_enter()
        return
    
    try:
        run_command(["sudo", "systemctl", "start", "webmin"])
        print(f"\n{Colors.GREEN}✅ Webmin service started successfully.{Colors.ENDC}")
        wait_for_enter()
        return True
    except subprocess.CalledProcessError:
        return False
    
def restart_webmin_service():
    """Restart the Webmin service"""
    try:
        run_command(["sudo", "systemctl", "restart", "webmin"])
        print(f"\n{Colors.GREEN}✅ Webmin service restarted successfully.{Colors.ENDC}")
        wait_for_enter()
        return True
    except subprocess.CalledProcessError:
        return False
    
def check_webmin_status():
    """Check the status of the Webmin service"""
    if not is_webmin_installed():
        print(f"\n{Colors.RED}❌ Webmin is not installed.{Colors.ENDC}")
        wait_for_enter()
        return
    
    try:
        result = subprocess.run(["sudo", "systemctl", "status", "webmin"], capture_output=True, text=True)
        status_lines = result.stdout.split('\n')
        
        # Extract active status and PID
        status_line = next((line for line in status_lines if "Active:" in line), "")
        pid_line = next((line for line in status_lines if "Main PID:" in line), "")
        
        if status_line and pid_line:
            status = "🟢 Running" if "active (running)" in status_line else "🔴 Stopped"
            pid = pid_line.split(':')[1].strip()
            
            print(f"\n{Colors.HEADER}{Colors.BOLD}{'═' * 15} Webmin Status {'═' * 15}{Colors.ENDC}")
            print(f"Status: {status}")
            print(f"PID: {pid}")
            print(f"{Colors.HEADER}{Colors.BOLD}{'═' * 45}{Colors.ENDC}")
        else:
            print(f"\n{Colors.RED}❌ Unable to get Webmin status{Colors.ENDC}")
            
        wait_for_enter()
        return True
    except subprocess.CalledProcessError:
        print(f"\n{Colors.RED}❌ Failed to get Webmin status{Colors.ENDC}")
        wait_for_enter()
        return False


def uninstall_webmin():
    """Uninstall Webmin and clean up related files with progress bars"""
    if not is_webmin_installed():
        print(f"\n{Colors.YELLOW}⚠️  Webmin is not installed.{Colors.ENDC}")
        wait_for_enter()
        return

    try:
        print(f"\n{Colors.BLUE}🗑️  Uninstalling Webmin...{Colors.ENDC}")
        
        # Stop service if running
        stop_webmin_service()
    
        # Remove Webmin packages with output display
        print(f"\n{Colors.BLUE}🗑️  Removing Webmin packages...{Colors.ENDC}")
        run_command(["sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "remove", "--purge", "-y", "webmin"])
        print(f"\n{Colors.GREEN}✅ Webmin packages removed successfully.{Colors.ENDC}")
        
        print(f"\n{Colors.BLUE}🗑️  Removing Webmin dependecies...{Colors.ENDC}")
        run_command(["sudo", "apt-get", "autoremove", "-y"])
        print(f"\n{Colors.GREEN}✅ Webmin dependecies removed successfully.{Colors.ENDC}")

        # Remove repository and configuration files
        if os.path.exists("/etc/apt/sources.list.d/webmin.list"):
            print(f"\n{Colors.BLUE}🗑️  Removing Webmin repository{Colors.ENDC}")            
            run_command(["sudo", "rm", "-f", "/etc/apt/sources.list.d/webmin.list"])
            print(f"\n{Colors.GREEN}✅ Webmin repository removed successfully.{Colors.ENDC}")
        # Remove configuration directories
        for path in ["/etc/webmin", "/var/webmin", "/var/log/webmin"]:
            if os.path.exists(path):
                print(f"\n{Colors.BLUE}🗑️  Removing {path}{Colors.ENDC}")                
                run_command(["sudo", "rm", "-rf", path])
                print(f"\n{Colors.GREEN}✅ {path} removed successfully.{Colors.ENDC}")

        # Update package list
        update_repositories()
        
        print(f"\n{Colors.GREEN}✅ Webmin has been successfully uninstalled and all related files have been removed.{Colors.ENDC}")
        wait_for_enter()
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during uninstallation: {e.stderr}")
        raise
    
def is_webmin_installed():
    """Check if Webmin is installed"""
    try:
        result = subprocess.run(["dpkg", "-l", "webmin"], capture_output=True, text=True)
        return "ii  webmin" in result.stdout
    except subprocess.CalledProcessError:
        return False
    
def is_webmin_running():
    """Check if Webmin is running"""
    try:
        result = subprocess.run(["systemctl", "is-active", "webmin"], capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
