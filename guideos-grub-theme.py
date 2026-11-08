#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =======================================================================
# Titel: GuideOS Grub Theme Selector
# Version: 1.0.5
# Autor: Nightworker
# Datum: 2025-12-25 (aktualisiert mit FileChooser-Vorschau & Autoskalierung)
# Beschreibung: Grafischer Grub-Theme-Manager mit Galerie-Vorschau
# Ein komfortables Werkzeug zum Verwalten von Grub-Bootloader-Themes.
# Das Programm zeigt Thumbnails aus /boot/grub/themes/ in einer
# klickbaren Galerie an und ermöglicht den Wechsel von Themes und Splash-Bildern.
# Lizenz: MIT
# ======================================================================

import os
import sys
import subprocess
import shlex
import tempfile
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk

# Konfiguration
GRUB_FILE = "/etc/default/grub"
THEMES_DIR = "/boot/grub/themes"
THUMB_SIZE = (250, 160)
PREVIEW_SIZE = (800, 500)
MAX_SPLASH_RES = (1920, 1080)

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

class GrubThemeSelector(Gtk.Window):
    def __init__(self):
        super().__init__(title="GuideOS GRUB Theme Selector")
        self.set_default_size(1300, 800)
        self.connect("destroy", Gtk.main_quit)

        self.themes = find_themes()
        self.active_theme_path = get_active_theme()
        self.theme_list = sorted(self.themes.keys(), key=str.lower)
        self.custom_splash_path = None
        self.temp_splash_file = None

        self.setup_ui()
        self.load_gallery()
        self.show_all()

    def __del__(self):
        if self.temp_splash_file and os.path.exists(self.temp_splash_file):
            try: os.remove(self.temp_splash_file)
            except: pass

    def setup_ui(self):
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.paned)

        # --- LINKE SEITE (Suche + Galerie) ---
        left_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_container.set_margin_start(5)
        left_container.set_margin_end(5)
        left_container.set_margin_top(5)
        left_container.set_margin_bottom(5)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Themes durchsuchen...")
        self.search_entry.connect("changed", self.on_search_changed)
        left_container.pack_start(self.search_entry, False, False, 5)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_width(320)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(1)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.connect("child-activated", self.on_flowbox_selected)
        self.flowbox.set_filter_func(self.filter_themes)

        scroll.add(self.flowbox)
        left_container.pack_start(scroll, True, True, 0)
        self.paned.pack1(left_container, False, False)

        # --- RECHTE SEITE (Vorschau & Controls) ---
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        right_box.set_margin_start(20)
        right_box.set_margin_end(20)
        right_box.set_margin_top(20)
        right_box.set_margin_bottom(10)

        self.preview_image = Gtk.Image()
        preview_aspect = Gtk.AspectFrame(label=None, xalign=0.5, yalign=0.5, ratio=1.6, obey_child=False)
        preview_aspect.set_shadow_type(Gtk.ShadowType.NONE)
        preview_aspect.add(self.preview_image)
        right_box.pack_start(preview_aspect, True, True, 0)

        selection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl = Gtk.Label(label="Gewähltes Theme:")
        selection_box.pack_start(lbl, False, False, 0)

        self.combo = Gtk.ComboBoxText()
        for name in self.theme_list:
            self.combo.append_text(name)
        self.combo.connect("changed", self.on_combo_changed)
        selection_box.pack_start(self.combo, True, True, 0)
        right_box.pack_start(selection_box, False, False, 0)

        # --- BEREICH: Eigenes Splash-Bild ---
        splash_frame = Gtk.Frame(label="Manuelles Splash-Bild (optional, max. 1920x1080)")
        splash_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        splash_box.set_margin_start(10)
        splash_box.set_margin_end(10)
        splash_box.set_margin_top(10)
        splash_box.set_margin_bottom(10)

        btn_choose_splash = Gtk.Button(label="Bild auswählen...")
        btn_choose_splash.connect("clicked", self.on_choose_custom_splash)

        btn_reset_splash = Gtk.Button(label="Zurücksetzen")
        btn_reset_splash.connect("clicked", self.on_reset_custom_splash)

        self.lbl_splash_info = Gtk.Label(label="Aktiv: Theme-Standardbild")
        self.lbl_splash_info.set_xalign(0.0)

        splash_box.pack_start(btn_choose_splash, False, False, 0)
        splash_box.pack_start(btn_reset_splash, False, False, 0)
        splash_box.pack_start(self.lbl_splash_info, True, True, 0)

        splash_frame.add(splash_box)
        right_box.pack_start(splash_frame, False, False, 0)

        # --- Aktions-Buttons ---
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_reload = Gtk.Button(label="Neu laden")
        btn_reload.connect("clicked", self.on_reload)
        btn_apply = Gtk.Button(label="Theme anwenden")
        btn_apply.get_style_context().add_class("suggested-action")
        btn_apply.connect("clicked", self.on_apply)
        btn_exit = Gtk.Button(label="Beenden")
        btn_exit.connect("clicked", Gtk.main_quit)

        btn_box.pack_start(btn_reload, False, False, 0)
        btn_box.pack_end(btn_exit, False, False, 0)
        btn_box.pack_end(btn_apply, False, False, 0)
        right_box.pack_start(btn_box, False, False, 0)

        self.statusbar = Gtk.Statusbar()
        self.status_context = self.statusbar.get_context_id("info")
        right_box.pack_start(self.statusbar, False, False, 0)

        self.paned.pack2(right_box, True, True)

    def load_gallery(self):
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)
        for name in self.theme_list:
            theme_dir = os.path.dirname(self.themes[name])
            img_path = find_preview_image(theme_dir)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_margin_bottom(15)
            if img_path:
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(img_path, THUMB_SIZE[0], THUMB_SIZE[1], True)
                    img_widget = Gtk.Image.new_from_pixbuf(pb)
                except:
                    img_widget = Gtk.Image.new_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
            else:
                img_widget = Gtk.Image.new_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
                img_widget.set_size_request(THUMB_SIZE[0], THUMB_SIZE[1])
            box.pack_start(img_widget, False, False, 0)
            box.pack_start(Gtk.Label(label=name), False, False, 0)
            child = Gtk.FlowBoxChild()
            child.theme_name = name
            child.add(box)
            self.flowbox.add(child)
        if self.active_theme_path:
            for i, name in enumerate(self.theme_list):
                if self.themes[name] == self.active_theme_path:
                    self.combo.set_active(i)
                    break
        self.show_all()

    def filter_themes(self, child):
        search_text = self.search_entry.get_text().lower()
        if not search_text: return True
        return search_text in child.theme_name.lower()

    def on_search_changed(self, entry):
        self.flowbox.invalidate_filter()

    def update_status(self, text):
        self.statusbar.push(self.status_context, text)

    def on_flowbox_selected(self, flowbox, child):
        if child:
            name = child.theme_name
            for i, n in enumerate(self.theme_list):
                if n == name:
                    self.combo.set_active(i)
                    break

    def on_combo_changed(self, combo):
        name = combo.get_active_text()
        if not name: return
        theme_txt = self.themes[name]
        img_path = find_preview_image(os.path.dirname(theme_txt))
        if img_path:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(img_path, PREVIEW_SIZE[0], PREVIEW_SIZE[1], True)
            self.preview_image.set_from_pixbuf(pb)
        self.update_status(f"Theme gewählt: {name}")

    def on_update_file_preview(self, file_chooser):
        filename = file_chooser.get_preview_filename()
        if filename and os.path.isfile(filename):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename, 220, 220, True)
                self.chooser_preview_image.set_from_pixbuf(pixbuf)
                file_chooser.set_preview_widget_active(True)
                return
            except:
                pass
        file_chooser.set_preview_widget_active(False)

    def on_choose_custom_splash(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Eigenes Splash-Bild auswählen (wird ggf. auf 1920x1080 skaliert)",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_img = Gtk.FileFilter()
        filter_img.set_name("Bilder (PNG, JPG)")
        filter_img.add_mime_type("image/png")
        filter_img.add_mime_type("image/jpeg")
        filter_img.add_pattern("*.png")
        filter_img.add_pattern("*.jpg")
        filter_img.add_pattern("*.jpeg")
        dialog.add_filter(filter_img)

        # Integrierte Bildvorschau für den Dateiauswahl-Dialog einrichten
        self.chooser_preview_image = Gtk.Image()
        dialog.set_preview_widget(self.chooser_preview_image)
        dialog.connect("update-preview", self.on_update_file_preview)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            orig_path = dialog.get_filename()
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(orig_path)
                orig_w = pixbuf.get_width()
                orig_h = pixbuf.get_height()

                target_w, target_h = MAX_SPLASH_RES

                if orig_w > target_w or orig_h > target_h:
                    ratio = min(target_w / orig_w, target_h / orig_h)
                    new_w = int(orig_w * ratio)
                    new_h = int(orig_h * ratio)
                    scaled_pixbuf = pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.BILINEAR)
                else:
                    scaled_pixbuf = pixbuf

                if self.temp_splash_file and os.path.exists(self.temp_splash_file):
                    try: os.remove(self.temp_splash_file)
                    except: pass

                fd, self.temp_splash_file = tempfile.mkstemp(suffix=".png", prefix="grub_splash_")
                os.close(fd)

                scaled_pixbuf.savev(self.temp_splash_file, "png", [], [])
                self.custom_splash_path = self.temp_splash_file

                filename = os.path.basename(orig_path)
                scale_info = f" (skaliert von {orig_w}x{orig_h})" if (orig_w > target_w or orig_h > target_h) else ""
                self.lbl_splash_info.set_text(f"Aktiv: {filename}{scale_info}")
                self.update_status(f"Eigenes Splash-Bild geladen und angepasst: {filename}")

            except Exception as e:
                self.update_status(f"Fehler beim Verarbeiten des Bildes: {str(e)}")

        dialog.destroy()

    def on_reset_custom_splash(self, btn):
        if self.temp_splash_file and os.path.exists(self.temp_splash_file):
            try: os.remove(self.temp_splash_file)
            except: pass
        self.temp_splash_file = None
        self.custom_splash_path = None
        self.lbl_splash_info.set_text("Aktiv: Theme-Standardbild")
        self.update_status("Eigenes Splash-Bild zurückgesetzt (nutze Theme-Standard).")

    def on_reload(self, btn):
        self.themes = find_themes()
        self.theme_list = sorted(self.themes.keys(), key=str.lower)
        self.combo.remove_all()
        for name in self.theme_list: self.combo.append_text(name)
        self.active_theme_path = get_active_theme()
        self.load_gallery()

    def on_apply(self, btn):
        name = self.combo.get_active_text()
        if not name: return
        theme_path = self.themes[name]
        theme_dir = os.path.dirname(theme_path)

        img_path = self.custom_splash_path if self.custom_splash_path else find_preview_image(theme_dir)

        settings = {
            "GRUB_THEME": f'"{theme_path}"',
            "GRUB_GFXMODE": "auto",
            "GRUB_DISABLE_OS_PROBER": "false"
        }

        bash_script = f"cp {GRUB_FILE} {GRUB_FILE}.backup && "

        if img_path:
            bash_script += f"cp {shlex.quote(img_path)} /boot/grub/splash.png && "

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
            subprocess.run(["pkexec", "bash", "-c", bash_script], check=True)
            self.update_status("Erfolgreich: Theme, Splash-Bild, GFX und OS-Prober gesetzt!")
        except subprocess.CalledProcessError:
            self.update_status("Fehler: Passwort falsch oder Abbruch.")
        except Exception as e:
            self.update_status(f"Unerwarteter Fehler: {str(e)}")

if __name__ == "__main__":
    app = GrubThemeSelector()
    Gtk.main()
