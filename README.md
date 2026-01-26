## ✨ Übersicht
Das Programm ist ein grafischer Grub-Theme-Manager, der installierte Bootloader-Themes übersichtlich in einer Galerie mit Thumbnail- und Großvorschau darstellt. Es ermöglicht das einfache Auswählen und Aktivieren von Grub-Themes aus dem\ 
Verzeichnis /boot/grub/themes/ per Mausklick.



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
