import subprocess
import os
import time
import sys
import itertools
import threading
import getpass
import crypt
from tqdm import tqdm
from common import update_system


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


def get_root_password():
    """Get the root user password"""
    try:
        with open('/etc/shadow', 'r') as f:
            for line in f:
                if line.startswith('root:'):
                    return True if line.split(':')[1] not in ['*', '!', ''] else False
    except:
        return False


def setup_webmin_repository(show_output: bool = False):
    """Set up Webmin repository manually without using the setup script"""
    try:
        # Add Webmin GPG key
        run_command_with_progress(
            ["sudo", "curl", "-fsSL", "http://www.webmin.com/jcameron-key.asc", "-o", "/usr/share/keyrings/webmin-keyring.asc"],
            "Downloading Webmin GPG key",
            5,
            show_output
        )

        # Add Webmin repository
        repo_line = "deb [signed-by=/usr/share/keyrings/webmin-keyring.asc] http://download.webmin.com/download/repository sarge contrib"
        with open("/tmp/webmin.list", "w") as f:
            f.write(repo_line)
        
        run_command_with_progress(
            ["sudo", "mv", "/tmp/webmin.list", "/etc/apt/sources.list.d/webmin.list"],
            "Adding Webmin repository",
            2,
            show_output
        )

        # Update package list
        run_command_with_progress(
            ["sudo", "apt-get", "update"],
            "Updating package list",
            10,
            show_output
        )

        return True
    except Exception as e:
        print(f"\n❌ Error setting up Webmin repository: {str(e)}")
        return False


def get_user_output_preference():
    """Ask user if they want to see command output"""
    while True:
        choice = input("\nDo you want to see detailed command output? (y/n): ").lower().strip()
        if choice in ['y', 'n']:
            return choice == 'y'
        print("Please enter 'y' for yes or 'n' for no.")


def create_webmin_user(show_output: bool = False):
    """Create a dedicated user for Webmin"""
    try:
        while True:
            create_user = input("\nDo you want to create a dedicated user for Webmin? (y/n): ").lower().strip()
            if create_user in ['y', 'n']:
                break
            print("Please enter 'y' for yes or 'n' for no.")

        if create_user == 'y':
            while True:
                username = input("\nEnter username for Webmin: ").strip()
                if username and not ' ' in username and len(username) >= 3:
                    break
                print("Username must be at least 3 characters and contain no spaces.")

            while True:
                password = getpass.getpass("Enter password for Webmin user: ")
                if len(password) >= 8:
                    password_confirm = getpass.getpass("Confirm password: ")
                    if password == password_confirm:
                        break
                    print("Passwords do not match. Please try again.")
                else:
                    print("Password must be at least 8 characters long.")

            # Create system user
            encrypted_pass = crypt.crypt(password)
            print("\n📝 Creating user account...")
            
            run_command_with_progress(
                ["sudo", "useradd", "-m", "-s", "/bin/bash", "-p", encrypted_pass, username],
                "Creating user account",
                3,
                show_output
            )

            # Add user to sudo group for Webmin access
            run_command_with_progress(
                ["sudo", "usermod", "-aG", "sudo", username],
                "Adding user to sudo group",
                2,
                show_output
            )

            return username, password
    except Exception as e:
        print(f"\n❌ Error creating Webmin user: {str(e)}")
        return None, None

    return None, None


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
    """Install Webmin with progress bars"""
    try:
        print("\n📦 Installing Webmin...")
        
        # Ask user about output visibility
        show_output = get_user_output_preference()
        if show_output:
            print("\n⚠️  Detailed command output will be shown.")
        else:
            print("\n⚠️  Only progress bars will be shown.")
        
        # Update system
        run_command_with_progress(
            ["sudo", "apt-get", "update"],
            "Updating system",
            10,
            show_output
        )
        
        # Set up Webmin repository
        print("\n⚙️  Setting up Webmin repository...")
        if not setup_webmin_repository(show_output):
            raise Exception("Failed to set up Webmin repository")
        
        # Install Webmin with output display
        print("\n📥 Installing Webmin packages...")
        run_command_with_progress(
            ["sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", "webmin", "--install-recommends"],
            "Installing Webmin packages",
            60,
            show_output
        )
        
        # Create Webmin user if requested
        webmin_user, webmin_pass = create_webmin_user(show_output)
        
        print("\n✅ Webmin installation completed successfully!")
        show_login_instructions(webmin_user, webmin_pass)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during installation: {e.stderr}")
        raise
    except Exception as e:
        print(f"\n❌ Error during installation: {str(e)}")
        raise


def is_webmin_installed():
    """Check if Webmin is installed"""
    try:
        result = subprocess.run(["dpkg", "-l", "webmin"], capture_output=True, text=True)
        return "ii  webmin" in result.stdout
    except subprocess.CalledProcessError:
        return False


def stop_webmin_service():
    """Stop the Webmin service"""
    try:
        run_command_with_progress(
            ["sudo", "systemctl", "stop", "webmin"],
            "Stopping Webmin service",
            5
        )
        return True
    except subprocess.CalledProcessError:
        return False


def uninstall_webmin():
    """Uninstall Webmin and clean up related files with progress bars"""
    if not is_webmin_installed():
        print("\n⚠️ Webmin is not installed.")
        return

    try:
        print("\n🗑️ Uninstalling Webmin...")
        
        # Ask user about output visibility
        show_output = get_user_output_preference()
        if show_output:
            print("\n⚠️  Detailed command output will be shown.")
        else:
            print("\n⚠️  Only progress bars will be shown.")
        
        # Stop service
        if stop_webmin_service():
            print("✅ Webmin service stopped successfully.")
        else:
            print("⚠️ Warning: Could not stop Webmin service. Continuing with uninstallation...")

        # Remove Webmin packages with output display
        run_command_with_progress(
            ["sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "remove", "--purge", "-y", "webmin"],
            "Removing Webmin packages",
            15,
            show_output
        )
        
        run_command_with_progress(
            ["sudo", "apt-get", "autoremove", "-y"],
            "Removing dependencies",
            10,
            show_output
        )

        # Remove repository and configuration files
        if os.path.exists("/etc/apt/sources.list.d/webmin.list"):
            run_command_with_progress(
                ["sudo", "rm", "-f", "/etc/apt/sources.list.d/webmin.list"],
                "Removing Webmin repository",
                2,
                show_output
            )

        # Remove configuration directories
        for path in ["/etc/webmin", "/var/webmin", "/var/log/webmin"]:
            if os.path.exists(path):
                run_command_with_progress(
                    ["sudo", "rm", "-rf", path],
                    f"Removing {path}",
                    3,
                    show_output
                )

        # Update package list
        run_command_with_progress(
            ["sudo", "apt-get", "update"],
            "Updating package list",
            10,
            show_output
        )

        print("\n✅ Webmin has been successfully uninstalled and all related files have been removed.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during uninstallation: {e.stderr}")
        raise
