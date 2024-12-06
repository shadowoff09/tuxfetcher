# 🐧 TuxFetcher

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://www.linux.org/)

TuxFetcher is a powerful Linux system administration tool that simplifies the installation and management of essential server services. It provides an interactive CLI interface for setting up BIND DNS Server and Webmin with minimal effort.

## 🚀 Features

### BIND DNS Server Management
- 🔧 Complete DNS server setup with forward and reverse zones
- 🔄 DNS forwarding configuration (defaults to Google DNS)
- 🛡️ Proper file permissions and service configuration
- ✅ Built-in configuration validation
- 🎯 Customizable settings for domains, IPs, and forwarders

### Webmin Installation
- 🌐 Automated Webmin setup from official repositories
- 📦 Includes recommended packages
- 🧹 Clean uninstallation option

## 📋 Prerequisites

- Linux-based operating system
- Root/sudo privileges
- Python 3.6 or higher
- Internet connection

## 💻 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tuxfetcher.git
cd tuxfetcher
```

2. Run the script with sudo privileges:
```bash
sudo python3 main.py
```

## 🎮 Usage

The interactive menu provides the following options:

```
===============Bind DNS Server================
1. Install BIND DNS Server
2. Uninstall BIND DNS Server
================Webmin===============
3. Install Webmin
4. Uninstall Webmin
0. Exit
```

### Setting up BIND DNS Server
When installing BIND, you'll be prompted for:
- Domain name (e.g., example.com)
- Reverse domain (e.g., 1.168.192.in-addr.arpa)
- DNS server IP address
- Admin email
- DNS forwarders (default: 8.8.8.8, 8.8.4.4)

### Installing Webmin
The Webmin installation is automated and will:
- Add the official Webmin repository
- Install Webmin with recommended packages
- Set up the web interface

## ⚠️ Warning

This tool is intended for development and testing environments. Additional security measures should be implemented for production use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🙏 Acknowledgments

- BIND DNS Server team
- Webmin development team

