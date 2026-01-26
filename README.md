# guideos-grub-theme
Graphical Grub Theme Manager with Gallery Preview\
A convenient tool for managing Grub bootloader themes.\
The program displays thumbnails from /boot/grub/themes/ in a clickable
gallery with large previews and allows you to easily change the active theme.


## 🔧 Installation

### Build from DEB Package:

```bash
# Clone repository
git clone https://github.com/Nightworker-DE/guideos-grub-theme.git
cd grub-theme

# Create DEB package
dpkg-buildpackage -us -uc

# Install (as root)
sudo dpkg -i
sudo apt-get install -f  # Resolve dependencies if needed
```
