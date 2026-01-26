## ✨ Overview
The program is a graphical GRUB theme manager that displays installed bootloader themes in a clear gallery with thumbnail and large preview. It allows users to easily select and activate GRUB themes from the /boot/grub/themes/ directory with a single click.

## 🔧 Installation

### Build from DEB Package:

```bash
# Clone repository
git clone https://github.com/Nightworker-DE/guideos-grub-theme.git
cd grub-theme

# Create DEB package
dpkg-buildpackage -us -uc

# Install (as root)
sudo dpkg -i ./guideos-grub-theme_1.0-1_all.deb
sudo apt-get install -f  # Resolve dependencies if needed
```
