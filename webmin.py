import subprocess

from common import update_system


def install_webmin():
    update_system()
    subprocess.run(["curl", "-o", "setup-repos.sh", "https://raw.githubusercontent.com/webmin/webmin/master/setup-repos.sh"])
    subprocess.run(["sudo", "sh", "setup-repos.sh"])
    subprocess.run(["sudo", "apt-get", "install", "-y", "webmin", "--install-recommends"])
    subprocess.run(["sudo", "rm", "setup-repos.sh"])



def uninstall_webmin():
    print('test')
