import subprocess


def update_system():
    print("Updating system packages...")
    subprocess.run(["sudo", "apt-get", "update"])
    subprocess.run(["sudo", "apt-get", "upgrade", "-y"])


def get_input(prompt, default):
    value = input(f"{prompt} [{default}]: ").strip()
    return value if value else default
