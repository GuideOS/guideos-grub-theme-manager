#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =======================================================================
# Titel: GuideOS Grub Theme Manager (PyQt6 Edition)
# Version: 1.0.9 (change in PyQt6)
# Autor: Nightworker
# Datum: 2026-11-13
# Beschreibung: Grafischer Grub-Theme-Manager mit Galerie-Vorschau in PyQt6
# Lizenz: GPLv3
# ======================================================================

import os
import sys
import subprocess
import shlex
import tempfile
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QImage
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QLineEdit, QListWidget, QListWidgetItem, QLabel,
    QComboBox, QPushButton, QGroupBox, QStatusBar, QFileDialog,
    QMessageBox, QInputDialog, QCheckBox, QScrollArea, QSizePolicy
)

# Konfiguration
GRUB_FILE = "/etc/default/grub"
THEMES_DIR = "/boot/grub/themes"
DEFAULT_THEME_RES = (2048, 1152)

def find_themes(themes_dir=THEMES_DIR):
    themes = {}
    if not os.path.exists(themes_dir): return themes
    for root, dirs, files in os.walk(themes_dir):
        rel = os.path.relpath(root, themes_dir)
        if rel.count(os.sep) > 1: continue
        if "theme.txt" in files:
            theme_name = os.path.basename(root)
            themes[theme_name] = os.path.join(root, "theme.txt")
    return themes

def get_active_theme(grub_file=GRUB_FILE):
    try:
        with open(grub_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GRUB_THEME="):
                    val = line.strip().split("=", 1)[1].strip()
                    return val.strip('"').strip("'")
    except: return None
    return None

def find_preview_image(theme_dir):
    candidates = ["preview.png", "preview.jpg", "background.png", "background.jpg"]
    for c in candidates:
        p = os.path.join(theme_dir, c)
        if os.path.isfile(p): return p
    return None

class GrubThemeSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GuideOS GRUB Theme Manager")

        # Auflösung des Hauptbildschirms ermitteln
        screen_geo = QApplication.primaryScreen().availableGeometry()
        screen_w = screen_geo.width()
        screen_h = screen_geo.height()

        # Dynamische Fenster- und Bildgrößen für kleine Bildschirme (z.B. 1366x768)
        if screen_w <= 1366 or screen_h <= 800:
            self.resize(min(1050, int(screen_w * 0.9)), min(650, int(screen_h * 0.85)))
            self.thumb_size = (180, 115)
            self.preview_size = (560, 350)
        else:
            self.resize(1300, 820)
            self.thumb_size = (250, 160)
            self.preview_size = (800, 500)

        self.themes = find_themes()
        self.active_theme_path = get_active_theme()
        self.theme_list = sorted(self.themes.keys(), key=str.lower)
        self.custom_splash_path = None
        self.temp_splash_file = None
        self.final_temp_splash = None

        self.setup_ui()
        self.load_gallery()

    def closeEvent(self, event):
        if self.temp_splash_file and os.path.exists(self.temp_splash_file):
            try: os.remove(self.temp_splash_file)
            except: pass
        if self.final_temp_splash and os.path.exists(self.final_temp_splash):
            try: os.remove(self.final_temp_splash)
            except: pass
        event.accept()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- LINKE SEITE (Suche + Galerie in Symbolansicht) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Themes durchsuchen...")
        self.search_entry.textChanged.connect(self.on_search_changed)
        left_layout.addWidget(self.search_entry)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(self.thumb_size[0], self.thumb_size[1]))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.currentItemChanged.connect(self.on_list_item_selected)
        left_layout.addWidget(self.list_widget)

        splitter.addWidget(left_widget)

        # --- RECHTE SEITE (Vorschau & Controls mit Scroll-Möglichkeit) ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        # Vorschau-Bild
        self.preview_image_label = QLabel()
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image_label.setStyleSheet("background-color: #222222; border-radius: 4px;")
        self.preview_image_label.setMinimumSize(320, 200)
        self.preview_image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.preview_image_label, stretch=1)

        # Theme Auswahl
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Gewähltes Theme:"))
        self.combo = QComboBox()
        for name in self.theme_list:
            self.combo.addItem(name)
        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        selection_layout.addWidget(self.combo, stretch=1)
        right_layout.addLayout(selection_layout)

        # --- BEREICH: Bildschirmauflösung & Skalierung ---
        res_group = QGroupBox("Ziel-Bildschirmauflösung für GRUB")
        res_layout = QVBoxLayout(res_group)

        self.chk_scale_resolution = QCheckBox("Auflösung anpassen (Aktivieren, um das Bild auf die Zielauflösung zu skalieren)")
        self.chk_scale_resolution.setChecked(False)
        self.chk_scale_resolution.toggled.connect(self.on_scale_toggled)
        res_layout.addWidget(self.chk_scale_resolution)

        hint_label = QLabel(
            "Hinweis: Standardmäßig werden alle Bilder in einem resourcenschonenden Format (2048x1152) belassen. "
            "Das Aktivieren höherer Auflösungen (z.B. 4K) kann zu einem deutlich höheren Speicherbedarf auf der /boot-Partition führen."
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        res_layout.addWidget(hint_label)

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Ziel-Auflösung:"))
        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems([
            "1920x1080 (FHD)",
            "2048x1152 (2K Kompromiss)",
            "2560x1440 (QHD)",
            "3840x2160 (4K / UHD)",
            "Benutzerdefiniert..."
        ])
        self.combo_resolution.setEnabled(False)
        self.combo_resolution.setCurrentIndex(1)
        combo_layout.addWidget(self.combo_resolution, stretch=1)
        res_layout.addLayout(combo_layout)

        right_layout.addWidget(res_group)

        # --- BEREICH: Eigenes Splash-Bild ---
        splash_group = QGroupBox("Manuelles Splash-Bild (optional)")
        splash_layout = QHBoxLayout(splash_group)

        btn_choose_splash = QPushButton("Bild auswählen...")
        btn_choose_splash.clicked.connect(self.on_choose_custom_splash)

        btn_reset_splash = QPushButton("Zurücksetzen")
        btn_reset_splash.clicked.connect(self.on_reset_custom_splash)

        self.lbl_splash_info = QLabel("Aktiv: Theme-Standardbild")

        splash_layout.addWidget(btn_choose_splash)
        splash_layout.addWidget(btn_reset_splash)
        splash_layout.addWidget(self.lbl_splash_info, stretch=1)
        right_layout.addWidget(splash_group)

        # --- Aktions-Buttons ---
        btn_layout = QHBoxLayout()
        btn_reload = QPushButton("Neu laden")
        btn_reload.clicked.connect(self.on_reload)
        btn_apply = QPushButton("Theme anwenden")
        btn_apply.setStyleSheet("font-weight: bold; background-color: #1b5e20; color: white; padding: 6px 12px;")
        btn_apply.clicked.connect(self.on_apply)
        btn_exit = QPushButton("Beenden")
        btn_exit.clicked.connect(self.close)

        btn_layout.addWidget(btn_reload)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_exit)
        right_layout.addLayout(btn_layout)

        # Scrollbereich für kleine Auflösungen integrieren
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(right_container)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        splitter.addWidget(scroll_area)

        left_width = max(280, int(self.width() * 0.3))
        right_width = self.width() - left_width
        splitter.setSizes([left_width, right_width])

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

    def on_scale_toggled(self, checked):
        self.combo_resolution.setEnabled(checked)

    def get_target_resolution(self):
        if not self.chk_scale_resolution.isChecked():
            return f"{DEFAULT_THEME_RES[0]}x{DEFAULT_THEME_RES[1]}"

        text = self.combo_resolution.currentText()
        if "Benutzerdefiniert" in text:
            custom_res, ok = QInputDialog.getText(
                self, "Benutzerdefinierte Auflösung",
                "Geben Sie die Auflösung ein (Format BxH, z.B. 2560x1080):",
                QLineEdit.EchoMode.Normal, "2048x1152"
            )
            if ok and custom_res:
                custom_res = custom_res.strip()
                if "x" in custom_res:
                    return custom_res
            return f"{DEFAULT_THEME_RES[0]}x{DEFAULT_THEME_RES[1]}"
        else:
            return text.split(" ")[0]

    def load_gallery(self):
        self.list_widget.clear()
        for name in self.theme_list:
            theme_dir = os.path.dirname(self.themes[name])
            img_path = find_preview_image(theme_dir)

            item = QListWidgetItem(name)
            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                scaled = pixmap.scaled(
                    self.thumb_size[0], self.thumb_size[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                item.setIcon(QIcon(scaled))

            self.list_widget.addItem(item)

        if self.active_theme_path:
            for i, name in enumerate(self.theme_list):
                if self.themes[name] == self.active_theme_path:
                    self.combo.setCurrentIndex(i)
                    break
        self.statusbar.showMessage("Galerie geladen.", 3000)

    def on_search_changed(self, text):
        search_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            match = search_text in item.text().lower()
            item.setHidden(not match)

    def on_list_item_selected(self, current, previous):
        if current:
            name = current.text()
            idx = self.combo.findText(name)
            if idx >= 0 and idx != self.combo.currentIndex():
                self.combo.setCurrentIndex(idx)

    def on_combo_changed(self, index):
        if index < 0: return
        name = self.combo.currentText()
        theme_txt = self.themes.get(name)
        if not theme_txt: return

        img_path = find_preview_image(os.path.dirname(theme_txt))
        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            scaled = pixmap.scaled(
                self.preview_size[0], self.preview_size[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_image_label.setPixmap(scaled)
        else:
            self.preview_image_label.clear()
            self.preview_image_label.setText("Keine Vorschau verfügbar")

        self.statusbar.showMessage(f"Theme gewählt: {name}", 3000)

    def on_choose_custom_splash(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Eigenes Splash-Bild auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg)"
        )
        if file_path:
            try:
                image = QImage(file_path)
                if image.isNull():
                    QMessageBox.warning(self, "Fehler", "Das Bild konnte nicht geladen werden.")
                    return

                if self.temp_splash_file and os.path.exists(self.temp_splash_file):
                    try: os.remove(self.temp_splash_file)
                    except: pass

                fd, self.temp_splash_file = tempfile.mkstemp(suffix=".png", prefix="grub_splash_")
                os.close(fd)

                image.save(self.temp_splash_file, "PNG")
                self.custom_splash_path = self.temp_splash_file

                filename = os.path.basename(file_path)
                self.lbl_splash_info.setText(f"Aktiv: {filename}")
                self.statusbar.showMessage(f"Eigenes Splash-Bild geladen: {filename}", 3000)

            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Verarbeiten des Bildes:\n{str(e)}")

    def on_reset_custom_splash(self):
        if self.temp_splash_file and os.path.exists(self.temp_splash_file):
            try: os.remove(self.temp_splash_file)
            except: pass
        self.temp_splash_file = None
        self.custom_splash_path = None
        self.lbl_splash_info.setText("Aktiv: Theme-Standardbild")
        self.statusbar.showMessage("Eigenes Splash-Bild zurückgesetzt.", 3000)

    def on_reload(self):
        self.themes = find_themes()
        self.theme_list = sorted(self.themes.keys(), key=str.lower)
        self.combo.clear()
        for name in self.theme_list:
            self.combo.addItem(name)
        self.active_theme_path = get_active_theme()
        self.load_gallery()

    def on_apply(self):
        name = self.combo.currentText()
        if not name: return
        theme_path = self.themes[name]
        theme_dir = os.path.dirname(theme_path)

        res_str = self.get_target_resolution()
        try:
            target_w, target_h = map(int, res_str.split("x"))
        except ValueError:
            target_w, target_h = DEFAULT_THEME_RES
            res_str = f"{DEFAULT_THEME_RES[0]}x{DEFAULT_THEME_RES[1]}"

        if not self.chk_scale_resolution.isChecked():
            target_w, target_h = DEFAULT_THEME_RES
            res_str_grub = "auto"
        else:
            res_str_grub = f"{res_str},auto"

        settings = {
            "GRUB_THEME": f'"{theme_path}"',
            "GRUB_GFXMODE": f'"{res_str_grub}"',
            "GRUB_DISABLE_OS_PROBER": "false"
        }

        # Korrektur: Keine Anführungszeichen um GRUB_FILE im bash-String, da es keine Leerzeichen hat
        bash_script = f"cp {GRUB_FILE} {GRUB_FILE}.backup && "

        source_img_path = self.custom_splash_path if self.custom_splash_path else find_preview_image(theme_dir)

        if source_img_path and os.path.exists(source_img_path):
            try:
                img = QImage(source_img_path)
                if not img.isNull():
                    scaled_img = img.scaled(target_w, target_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

                    if self.final_temp_splash and os.path.exists(self.final_temp_splash):
                        try: os.remove(self.final_temp_splash)
                        except: pass

                    fd, self.final_temp_splash = tempfile.mkstemp(suffix=".png", prefix="grub_final_splash_")
                    os.close(fd)
                    scaled_img.save(self.final_temp_splash, "PNG")

                    bash_script += f"cp {shlex.quote(self.final_temp_splash)} /boot/grub/splash.png && "
            except Exception as e:
                print(f"Fehler beim Verarbeiten des Splash-Bildes: {e}")

        for key, value in settings.items():
            bash_script += (
                f"if grep -q '^#\\?{key}=' {GRUB_FILE}; then "
                f"  sed -i 's|^#\\?{key}=.*|{key}={value}|' {GRUB_FILE}; "
                f"else "
                f"  echo '{key}={value}' >> {GRUB_FILE}; "
                f"fi && "
            )

        bash_script += "update-grub"

        try:
            result = subprocess.run(["pkexec", "bash", "-c", bash_script], capture_output=True, text=True)
            if result.returncode == 0:
                self.statusbar.showMessage("Erfolgreich: Theme, Splash-Bild und Einstellungen angewendet!", 5000)
                QMessageBox.information(self, "Erfolg", "Das GRUB-Theme wurde erfolgreich angewendet!")
            else:
                QMessageBox.warning(self, "Fehler", f"Befehl fehlgeschlagen:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Kritischer Fehler", f"Unerwarteter Fehler:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    selector = GrubThemeSelector()
    selector.show()
    sys.exit(app.exec())
