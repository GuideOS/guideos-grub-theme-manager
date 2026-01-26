# guideos-grub-theme
Grafischer Grub-Theme-Manager mit Galerie-Vorschau \
Ein komfortables Werkzeug zum Verwalten von Grub-Bootloader-Themes. \
Das Programm zeigt Thumbnails aus /boot/grub/themes/ in einer klickbaren \
Galerie mit großer Vorschau an und ermöglicht den einfachen Wechsel \
des aktiven Themes.


## 🔧 Installation

### Build from DEB Package:

```bash
# Clone repository
git clone https://github.com/GuideOS/primo-di-tutto.git
cd primo-di-tutto

# Create DEB package
dpkg-source --build ./

# Install (as root)
sudo dpkg -i ../primo_*.deb
sudo apt-get install -f  # Resolve dependencies if needed
```
