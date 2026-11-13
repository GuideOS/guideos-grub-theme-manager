## ✨ Übersicht
### GuideOS GRUB Theme Selector (PyQt6 Edition)   
Ein moderner, grafischer Theme-Manager für GRUB2, entwickelt mit PyQt6. Mit diesem Tool kannst du   
GRUB-Themes komfortabel verwalten, in einer visuellen Galerie betrachten, Auflösungen anpassen und   
mit wenigen Klicks sicher auf deinem System anwenden.    
🚀 HauptmerkmaleVisuelle Galerie-Vorschau:   
Durchsuche alle installierten Themes unter /boot/grub/themes mit automatischer Erkennung von   
Vorschaubildern (preview.png, background.png etc.).   
Echtzeit-Suche: 
Finde bestimmte Themes blitzschnell über die integrierte Suchleiste.   
Bildschirmauflösung & Skalierung:   
Passe die GRUB-Auflösung (GRUB_GFXMODE) flexibel an – wähle zwischen vordefinierten Profilen   
(FHD, QHD, 4K) oder benutzerdefinierten Werten.   
Eigene Splash-Bilder:   
Lade optional eigene Hintergrundbilder hoch, die automatisch skaliert und als GRUB-Splash-Bild eingerichtet werden.   
Sichere Rechteverwaltung:   
Führt administrative Befehle (update-grub, Bearbeitung von /etc/default/grub) sicher über pkexec und mit   
automatischer Backup-Erstellung (grub.backup) aus.   
Responsive Oberfläche:   
Passt sich dynamisch an verschiedene Bildschirmgrößen an   
(optimiert für kleine Laptops bis hin zu hochauflösenden 4K-Monitoren).    
🛠️ Voraussetzungen   
Eine Linux-Distribution mit GRUB2 als BootloaderPython 3PyQt6Root-Rechte   
(wird via Polkit / pkexec für die Systemänderungen abgefragt)

<div style="display:flex; gap:10px;">
  <img src="screenshot.webp" width="700">
</div>
