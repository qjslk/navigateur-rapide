# /chemin/vers/votre/projet/mon_navigateur.py
import sys
import logging
import os
import subprocess
import winreg
from PyQt6.QtCore import QUrl, QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QStatusBar,
    QSplitter,
    QFrame,
    QLabel,
    QDialog,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QFormLayout,
    QDialogButtonBox,
    QTabWidget,
    QTextEdit,
    QInputDialog,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QAction, QCloseEvent
from updater import setup_auto_updater
from live_updater import setup_live_updater
from version import get_version, get_app_info, get_github_repo_url, CONFIG_FILE, DEFAULT_REPO
from typing import TYPE_CHECKING, Optional
from telemetry_client import start_telemetry_client
import pyperclip
import pyautogui
import cv2
from pyzbar.pyzbar import decode as decode_qr
import pyttsx3
import psutil
from plyer import notification
import pandas as pd
import humanize
from bs4 import BeautifulSoup
import bs4
import io
import datetime
import rich
from rich.console import Console
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from service_monitor import start_monitor, get_status_report

# Configuration basique du journal (enregistre dans un fichier)
logging.basicConfig(filename='browser_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Demarrage de l'application")


class SettingsDialog(QDialog):
    """Fenêtre de paramètres pour Retrosoft"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window: Optional["MainWindow"] = None  # Typage explicite pour Pyright
        self.setWindowTitle("⚙️ Paramètres - Retrosoft")
        self.setFixedSize(500, 400)
        self.setWindowIcon(QIcon("icons/browser.svg"))
        import json, os
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.config = self.load_config()
        # Layout principal
        layout = QVBoxLayout()
        # Onglets
        tabs = QTabWidget()
        # Onglet Général
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "🏠 Général")
        # Onglet Mise à jour
        update_tab = self.create_update_tab()
        tabs.addTab(update_tab, "🔄 Mise à jour")
        # Onglet Avancé
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "🛠️ Avancé")
        # Onglet À propos
        about_tab = self.create_about_tab()
        tabs.addTab(about_tab, "ℹ️ À propos")
        layout.addWidget(tabs)
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self):
        import json
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def create_general_tab(self):
        """Crée l'onglet des paramètres généraux"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Groupe Navigation
        nav_group = QGroupBox("🌐 Navigation")
        nav_layout = QFormLayout()
        
        # Page d'accueil
        self.homepage_combo = QComboBox()
        self.homepage_combo.addItems([
            "Page d'accueil locale",
            "Google",
            "Bing",
            "DuckDuckGo",
            "Page vierge"
        ])
        nav_layout.addRow("Page d'accueil:", self.homepage_combo)
        
        # Moteur de recherche par défaut
        self.search_engine = QComboBox()
        self.search_engine.addItems([
            "Google",
            "Bing",
            "DuckDuckGo",
            "Yahoo"
        ])
        nav_layout.addRow("Moteur de recherche:", self.search_engine)
        
        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)
        
        # Groupe Interface
        ui_group = QGroupBox("🎨 Interface")
        ui_layout = QFormLayout()
        
        # Afficher la sidebar au démarrage
        self.show_sidebar = QCheckBox("Afficher la sidebar au démarrage")
        self.show_sidebar.setChecked(True)
        ui_layout.addRow(self.show_sidebar)
        
        # Taille de la fenêtre
        self.window_size = QComboBox()
        self.window_size.addItems([
            "1200x800 (Défaut)",
            "1024x768",
            "1366x768",
            "1920x1080",
            "Maximisée"
        ])
        ui_layout.addRow("Taille de fenêtre:", self.window_size)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # Groupe Système
        system_group = QGroupBox("🖥️ Système")
        system_layout = QVBoxLayout()
        
        # Bouton pour définir comme navigateur par défaut
        default_browser_btn = QPushButton("🌐 Définir comme navigateur par défaut")
        default_browser_btn.clicked.connect(self.set_as_default_browser)
        default_browser_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        system_layout.addWidget(default_browser_btn)
        
        # Statut du navigateur par défaut
        self.default_status_label = QLabel()
        self.update_default_browser_status()
        system_layout.addWidget(self.default_status_label)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_update_tab(self):
        """Crée l'onglet des paramètres de mise à jour"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Groupe Mise à jour automatique
        update_group = QGroupBox("🔄 Mise à jour automatique")
        update_layout = QFormLayout()
        
        # Vérification automatique
        self.auto_check = QCheckBox("Vérifier automatiquement les mises à jour")
        self.auto_check.setChecked(True)
        update_layout.addRow(self.auto_check)
        
        # Fréquence de vérification
        self.check_frequency = QComboBox()
        self.check_frequency.addItems([
            "À chaque démarrage",
            "Quotidienne",
            "Hebdomadaire",
            "Mensuelle"
        ])
        update_layout.addRow("Fréquence:", self.check_frequency)
        
        # Téléchargement automatique
        self.auto_download = QCheckBox("Télécharger automatiquement les mises à jour")
        update_layout.addRow(self.auto_download)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        # Groupe Version actuelle
        version_group = QGroupBox("📋 Version actuelle")
        version_layout = QVBoxLayout()
        
        app_info = get_app_info()
        version_text = f"""
        <b>Nom:</b> {app_info['name']}<br>
        <b>Version:</b> {app_info['version']}<br>
        <b>Description:</b> {app_info['description']}<br>
        <b>Repository:</b> {app_info['repo']}
        """
        
        version_label = QLabel(version_text)
        version_label.setWordWrap(True)
        version_layout.addWidget(version_label)
        
        # Boutons de vérification
        buttons_layout = QHBoxLayout()
        
        check_now_btn = QPushButton("🔍 Vérifier maintenant")
        check_now_btn.clicked.connect(self.check_updates_now)
        buttons_layout.addWidget(check_now_btn)
        
        live_check_btn = QPushButton("⚡ Vérifier mises à jour code")
        live_check_btn.clicked.connect(self.check_live_updates_now)
        live_check_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        buttons_layout.addWidget(live_check_btn)
        
        version_layout.addLayout(buttons_layout)
        
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        # Groupe GitHub
        github_group = QGroupBox("🔗 Dépôt GitHub")
        github_layout = QFormLayout()
        self.github_url_edit = QLineEdit(self.config.get("github_repo", ""))
        github_layout.addRow("URL du dépôt:", self.github_url_edit)
        test_btn = QPushButton("Tester l'URL")
        test_btn.clicked.connect(self.test_github_url)
        github_layout.addRow(test_btn)
        github_group.setLayout(github_layout)
        layout.addWidget(github_group)
        # Groupe Notifications
        notif_group = QGroupBox("🔔 Notifications temps réel")
        notif_layout = QFormLayout()
        self.notif_url_edit = QLineEdit(self.config.get("notifier_url", "ws://localhost:8000/ws"))
        notif_layout.addRow("URL serveur:", self.notif_url_edit)
        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)
        # Groupe Options
        options_group = QGroupBox("⚙️ Options avancées")
        options_layout = QVBoxLayout()
        self.cb_telemetry = QCheckBox("Activer la télémétrie")
        self.cb_telemetry.setChecked(self.config.get("telemetry_enabled", True))
        self.cb_sync = QCheckBox("Activer la synchronisation auto")
        self.cb_sync.setChecked(self.config.get("sync_enabled", True))
        self.cb_notify = QCheckBox("Activer les notifications temps réel")
        self.cb_notify.setChecked(self.config.get("notify_enabled", True))
        options_layout.addWidget(self.cb_telemetry)
        options_layout.addWidget(self.cb_sync)
        options_layout.addWidget(self.cb_notify)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        # Groupe Logs/Historiques
        logs_group = QGroupBox("📝 Logs & Historique")
        logs_layout = QHBoxLayout()
        logs_btn = QPushButton("Afficher les logs")
        logs_btn.clicked.connect(self.show_logs_popup)
        histo_btn = QPushButton("Afficher l'historique")
        histo_btn.clicked.connect(self.show_history_popup)
        logs_layout.addWidget(logs_btn)
        logs_layout.addWidget(histo_btn)
        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_about_tab(self):
        """Crée l'onglet À propos"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Logo et titre
        title = QLabel("<h1>🚀 Retrosoft</h1>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        description = QTextEdit()
        description.setReadOnly(True)
        description.setMaximumHeight(200)
        
        about_text = f"""
<h3>Navigateur web moderne et rapide</h3>

<b>Version:</b> {get_version()}<br>
<b>Développé avec:</b> Python 3.11 + PyQt6<br>
<b>Moteur web:</b> Chromium (via QtWebEngine)<br>

<h4>🎯 Fonctionnalités:</h4>
• Interface moderne et intuitive<br>
• Sidebar avec raccourcis rapides<br>
• Système de mise à jour automatique<br>
• Page d'accueil personnalisée<br>
• Navigation rapide et fluide<br>

<h4>🔧 Technologies utilisées:</h4>
• PyQt6 pour l'interface utilisateur<br>
• QtWebEngine pour le rendu web<br>
• Requests pour les mises à jour<br>
• PyInstaller pour la distribution<br>

<h4>📞 Support:</h4>
Pour signaler un bug ou suggérer une amélioration,<br>
visitez notre repository GitHub.
        """
        
        description.setHtml(about_text)
        layout.addWidget(description)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        github_btn = QPushButton("🐙 GitHub")
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/qjslk/navigateur-rapide"))
        buttons_layout.addWidget(github_btn)
        
        license_btn = QPushButton("📄 Licence")
        license_btn.clicked.connect(self.show_license)
        buttons_layout.addWidget(license_btn)
        
        layout.addLayout(buttons_layout)
        
        widget.setLayout(layout)
        return widget
    
    def check_updates_now(self):
        """Vérifie les mises à jour maintenant"""
        if self.main_window and hasattr(self.main_window, 'updater'):
            self.main_window.updater.check_for_updates(silent=False)
    
    def check_live_updates_now(self):
        """Vérifie les mises à jour de code en temps réel"""
        if self.main_window and hasattr(self.main_window, 'live_updater'):
            self.main_window.live_updater.check_for_updates_manual()
    
    def open_url(self, url):
        """Ouvre une URL dans le navigateur parent"""
        if self.main_window and hasattr(self.main_window, 'browser'):
            self.main_window.browser.setUrl(QUrl(url))
            self.close()
    
    def show_license(self):
        """Affiche la licence"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Licence",
            "Retrosoft est distribué sous licence MIT.\n\n"
            "Vous êtes libre d'utiliser, modifier et distribuer\n"
            "ce logiciel selon les termes de cette licence."
        )
    
    def set_as_default_browser(self):
        """Définit Retrosoft comme navigateur par défaut"""
        from PyQt6.QtWidgets import QMessageBox
        
        # D'abord, enregistrer Retrosoft comme navigateur
        success = self.register_as_browser()
        
        if success:
            try:
                # Ouvre les paramètres Windows pour choisir les applications par défaut
                subprocess.run(['ms-settings:defaultapps'], shell=True)
                
                QMessageBox.information(
                    self,
                    "Navigateur par défaut",
                    "✅ Retrosoft a été enregistré comme navigateur !\n\n"
                    "Les paramètres Windows se sont ouverts.\n"
                    "Pour définir Retrosoft comme navigateur par défaut :\n\n"
                    "1. Cliquez sur 'Navigateur web'\n"
                    "2. Sélectionnez 'Retrosoft' dans la liste\n"
                    "3. Fermez les paramètres"
                )
                
            except Exception as e:
                # Méthode alternative : ouvrir directement les associations de fichiers
                try:
                    subprocess.run(['control', '/name', 'Microsoft.DefaultPrograms', '/page', 'pageDefaultProgram'], shell=True)
                    QMessageBox.information(
                        self,
                        "Navigateur par défaut",
                        "✅ Retrosoft a été enregistré comme navigateur !\n\n"
                        "Les paramètres de programmes par défaut se sont ouverts.\n"
                        "Sélectionnez Retrosoft et cliquez sur 'Définir ce programme comme programme par défaut'."
                    )
                except Exception as e2:
                    QMessageBox.information(
                        self,
                        "Navigateur enregistré",
                        "✅ Retrosoft a été enregistré comme navigateur !\n\n"
                        "Vous pouvez maintenant le définir comme navigateur par défaut dans :\n"
                        "Paramètres Windows > Applications > Applications par défaut > Navigateur web"
                    )
        else:
            QMessageBox.warning(
                self,
                "Erreur",
                "❌ Impossible d'enregistrer Retrosoft comme navigateur.\n\n"
                "Essayez de lancer l'application en tant qu'administrateur."
            )
        
        # Mettre à jour le statut après un délai
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, self.update_default_browser_status)
    
    def register_as_browser(self):
        """Enregistre Retrosoft comme navigateur dans le registre Windows"""
        try:
            # Chemin vers l'exécutable
            if getattr(sys, 'frozen', False):
                # Si l'application est compilée avec PyInstaller
                exe_path = sys.executable
            else:
                # Si on exécute le script Python
                exe_path = os.path.abspath(__file__)
            
            app_name = "Retrosoft"
            app_description = "Navigateur web rapide et moderne"
            prog_id = f"{app_name}.HTML"
            
            # 1. Enregistrer l'application
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\{app_name}") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, app_description)
                winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, exe_path)
            
            # 2. Enregistrer comme navigateur web dans la liste des clients
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, app_name)
            
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}\\Capabilities") as key:
                winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, app_name)
                winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ, app_description)
            
            # Associations d'URL
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}\\Capabilities\\URLAssociations") as key:
                winreg.SetValueEx(key, "http", 0, winreg.REG_SZ, f"{app_name}URL")
                winreg.SetValueEx(key, "https", 0, winreg.REG_SZ, f"{app_name}URL")
            
            # Commande par défaut
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}\\shell\\open\\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{exe_path}"')
            
            # 3. Créer les associations pour les protocoles
            for protocol in ["http", "https"]:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{app_name}URL") as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{app_name} URL")
                    winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
                
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{app_name}URL\\shell\\open\\command") as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
            
            logging.info("Retrosoft enregistré comme navigateur web")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement du navigateur : {e}")
            return False
    
    def update_default_browser_status(self):
        """Met à jour le statut du navigateur par défaut"""
        try:
            # Vérifier si Retrosoft est le navigateur par défaut
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
                prog_id = winreg.QueryValueEx(key, "ProgId")[0]
                
            if "Retrosoft" in prog_id or "NavigateurRapide" in prog_id:
                self.default_status_label.setText("✅ Retrosoft est votre navigateur par défaut")
                self.default_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.default_status_label.setText("❌ Retrosoft n'est pas votre navigateur par défaut")
                self.default_status_label.setStyleSheet("color: orange; font-weight: bold;")
                
        except Exception:
            self.default_status_label.setText("❓ Statut du navigateur par défaut inconnu")
            self.default_status_label.setStyleSheet("color: gray;")

    def test_github_url(self):
        import requests
        url = self.github_url_edit.text().strip()
        if not url:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Test GitHub", "Veuillez entrer une URL.")
            return
        try:
            if url.startswith("https://github.com/"):
                repo_path = url.replace("https://github.com/", "").strip("/")
                api_url = f"https://api.github.com/repos/{repo_path}"
                r = requests.get(api_url, timeout=5)
                if r.status_code == 200:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(self, "Test GitHub", "Connexion réussie !")
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Test GitHub", f"Erreur : {r.status_code}")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Test GitHub", "URL non valide.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Test GitHub", f"Erreur : {e}")

    def show_logs_popup(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
        dlg = QDialog(self)
        dlg.setWindowTitle("Logs Retrosoft")
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setReadOnly(True)
        import os
        log_path = os.path.join(os.path.dirname(__file__), "browser_log.txt")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                text.setText(f.read()[-10000:])
        else:
            text.setText("Aucun log trouvé.")
        layout.addWidget(text)
        dlg.setLayout(layout)
        dlg.resize(700, 500)
        dlg.exec()

    def show_history_popup(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
        dlg = QDialog(self)
        dlg.setWindowTitle("Historique des synchronisations")
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setReadOnly(True)
        import os
        histo_path = os.path.join(os.path.dirname(__file__), "update_history.json")
        if os.path.exists(histo_path):
            import pandas as pd
            try:
                df = pd.read_json(histo_path)
                text.setText(df.to_string())
            except Exception as e:
                text.setText(f"Erreur lecture historique : {e}")
        else:
            text.setText("Aucun historique trouvé.")
        layout.addWidget(text)
        dlg.setLayout(layout)
        dlg.resize(700, 500)
        dlg.exec()

    def save_and_accept(self):
        # Sauvegarder les paramètres avancés
        self.config["github_repo"] = self.github_url_edit.text().strip()
        self.config["notifier_url"] = self.notif_url_edit.text().strip()
        self.config["telemetry_enabled"] = self.cb_telemetry.isChecked()
        self.config["sync_enabled"] = self.cb_sync.isChecked()
        self.config["notify_enabled"] = self.cb_notify.isChecked()
        self.save_config()
        self.accept()


class LogViewerDialog(QDialog):
    def __init__(self, parent=None, log_path="browser_log.txt"):
        super().__init__(parent)
        self.setWindowTitle("Console Live - Logs Retrosoft")
        self.resize(900, 600)
        layout = QVBoxLayout()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        self.setLayout(layout)
        self.log_path = log_path
        from PyQt6.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_log)
        self.timer.start(1500)
        self.refresh_log()
    def refresh_log(self):
        import os
        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                self.text.setText(f.read()[-20000:])
        else:
            self.text.setText("Aucun log trouvé.")

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # --- Définir la page d'accueil locale ---
        logging.info("Definition de la page d'accueil")
        # Recherche robuste de accueil.html
        possible_paths = []
        if getattr(sys, 'frozen', False):
            app_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            possible_paths.append(os.path.join(app_dir, "accueil.html"))
            possible_paths.append(os.path.join(os.path.dirname(sys.executable), "accueil.html"))
        possible_paths.append(os.path.join(os.getcwd(), "accueil.html"))
        accueil_path = None
        for path in possible_paths:
            if os.path.exists(path):
                accueil_path = path
                break
        if accueil_path:
            self.home_page_url = QUrl.fromLocalFile(accueil_path)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", "Le fichier accueil.html est introuvable. L'application ne peut pas afficher la page d'accueil.")
            self.home_page_url = QUrl("about:blank")

        # --- Fenêtre principale ---
        self.setWindowTitle("Retrosoft")
        self.setWindowIcon(QIcon("icons/browser.svg")) # On utilise notre nouvelle icône SVG
        self.resize(1200, 800)

        logging.info("Creation de la vue web")
        # --- Vue Web ---
        self.browser = QWebEngineView()
        
        # Vérifier si une URL a été passée en argument
        if len(sys.argv) > 1:
            url_arg = sys.argv[1]
            if url_arg.startswith(('http://', 'https://')):
                self.browser.setUrl(QUrl(url_arg))
                logging.info(f"URL passée en argument : {url_arg}")
            else:
                self.browser.setUrl(self.home_page_url)
        else:
            self.browser.setUrl(self.home_page_url)

        logging.info("Creation de la barre d'outils")
        # --- Barre d'outils de navigation ---
        nav_toolbar = QToolBar("Navigation")
        nav_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(nav_toolbar)

        # Bouton Précédent
        back_btn = QAction(QIcon.fromTheme("go-previous"), "Précédent", self)
        back_btn.setStatusTip("Aller à la page précédente")
        back_btn.triggered.connect(self.browser.back)
        nav_toolbar.addAction(back_btn)

        # Bouton Suivant
        next_btn = QAction(QIcon.fromTheme("go-next"), "Suivant", self)
        next_btn.setStatusTip("Aller à la page suivante")
        next_btn.triggered.connect(self.browser.forward)
        nav_toolbar.addAction(next_btn)

        # Bouton Recharger
        reload_btn = QAction(QIcon.fromTheme("view-refresh"), "Recharger", self)
        reload_btn.setStatusTip("Recharger la page")
        reload_btn.triggered.connect(self.browser.reload)
        nav_toolbar.addAction(reload_btn)

        # Bouton Accueil
        home_btn = QAction(QIcon.fromTheme("go-home"), "Accueil", self)
        home_btn.setStatusTip("Aller à la page d'accueil")
        home_btn.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(home_btn)

        # Bouton Sidebar
        sidebar_btn = QAction(QIcon.fromTheme("view-list-details"), "Sidebar", self)
        sidebar_btn.setStatusTip("Afficher/Masquer la sidebar")
        sidebar_btn.triggered.connect(self.toggle_sidebar)
        nav_toolbar.addAction(sidebar_btn)

        # Bouton Console Live
        log_btn = QAction(QIcon.fromTheme("utilities-terminal"), "Console Live", self)
        log_btn.setStatusTip("Afficher la console de logs en direct")
        log_btn.triggered.connect(self.show_log_viewer)
        nav_toolbar.addAction(log_btn)
        # Bouton Diagnostic
        diag_btn = QAction(QIcon.fromTheme("dialog-information"), "Diagnostic", self)
        diag_btn.setStatusTip("Afficher l'état des services (auto-diagnostic)")
        diag_btn.triggered.connect(self.show_diagnostic)
        nav_toolbar.addAction(diag_btn)

        nav_toolbar.addSeparator()

        logging.info("Creation de la barre d'adresse")
        # --- Barre d'adresse ---
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url) # Naviguer avec la touche Entrée
        nav_toolbar.addWidget(self.url_bar)

        # Mettre à jour la barre d'adresse quand l'URL change
        self.browser.urlChanged.connect(self.update_url_bar)
        
        logging.info("Creation de la barre de statut")
        # --- Barre de statut ---
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        # Indicateurs d'état
        self.status_conn = QLabel("🌐 Connexion : ...")
        self.status_sync = QLabel("🔄 Sync : ...")
        self.status_notify = QLabel("🔔 Notif : ...")
        self.status_telemetry = QLabel("📡 Télémétrie : ...")
        self.status.addPermanentWidget(self.status_conn)
        self.status.addPermanentWidget(self.status_sync)
        self.status.addPermanentWidget(self.status_notify)
        self.status.addPermanentWidget(self.status_telemetry)
        # Timer de rafraîchissement
        from PyQt6.QtCore import QTimer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_status_indicators)
        self.status_timer.start(10000)  # 10 secondes
        self.refresh_status_indicators()
        
        logging.info("Creation de la sidebar")
        # --- Sidebar ---
        self.create_sidebar()
        
        # --- Layout principal avec splitter ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.browser)
        
        # Définir les tailles initiales (sidebar 200px, browser le reste)
        self.splitter.setSizes([200, 1000])
        
        # --- Affichage ---
        self.setCentralWidget(self.splitter)
        
        # --- Système de mise à jour automatique ---
        self.updater = setup_auto_updater(self, version=get_version())
        
        # --- Système de mise à jour en temps réel ---
        self.live_updater = setup_live_updater(self, version=get_version(), auto_check_minutes=2)
        logging.info("Système de mise à jour en temps réel activé (vérification toutes les 2 minutes)")
        # --- Vérification et synchronisation automatique des fichiers au démarrage ---
        self.check_and_update_files()

    def create_sidebar(self):
        """Crée la sidebar avec des boutons utiles."""
        self.sidebar = QFrame()
        self.sidebar.setFrameStyle(QFrame.Shape.StyledPanel)
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setMinimumWidth(150)
        
        layout = QVBoxLayout()
        
        # Titre de la sidebar
        title = QLabel("Retrosoft")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(title)
        
        # Boutons de navigation rapide
        sites_populaires = [
            ("🏠 Accueil", self.navigate_home),
            ("🔍 Google", lambda: self.navigate_to_site("https://www.google.com")),
            ("📺 YouTube", lambda: self.navigate_to_site("https://www.youtube.com")),
            ("📧 Gmail", lambda: self.navigate_to_site("https://mail.google.com")),
            ("💼 LinkedIn", lambda: self.navigate_to_site("https://www.linkedin.com")),
            ("🐦 Twitter", lambda: self.navigate_to_site("https://twitter.com")),
            ("📘 Facebook", lambda: self.navigate_to_site("https://www.facebook.com")),
            ("📰 Actualités", lambda: self.navigate_to_site("https://news.google.com")),
        ]
        
        for nom, action in sites_populaires:
            btn = QPushButton(nom)
            btn.clicked.connect(action)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    margin: 2px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)
            layout.addWidget(btn)

        # Bouton Historique
        history_btn = QPushButton("🕑 Historique")
        history_btn.clicked.connect(self.show_history)
        history_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                margin: 2px;
                border: 1px solid #17a2b8;
                border-radius: 4px;
                background-color: #e3f7fc;
                color: #117a8b;
            }
            QPushButton:hover {
                background-color: #c1e7f5;
            }
            QPushButton:pressed {
                background-color: #b3d9ff;
            }
        """)
        layout.addWidget(history_btn)
        
        # Bouton Paramètres
        settings_btn = QPushButton("⚙️ Paramètres")
        settings_btn.clicked.connect(self.open_settings)
        settings_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                margin: 2px;
                border: 1px solid #6c757d;
                border-radius: 4px;
                background-color: #f8f9fa;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        layout.addWidget(settings_btn)
        
        # Bouton de mise à jour
        update_btn = QPushButton("🔄 Vérifier les mises à jour")
        update_btn.clicked.connect(lambda: self.updater.check_for_updates(silent=False))
        update_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                margin: 2px;
                border: 1px solid #007bff;
                border-radius: 4px;
                background-color: #e7f3ff;
                color: #0056b3;
            }
            QPushButton:hover {
                background-color: #cce7ff;
            }
            QPushButton:pressed {
                background-color: #b3d9ff;
            }
        """)
        layout.addWidget(update_btn)
        
        # Bouton Copier l'URL
        copy_url_btn = QPushButton("📋 Copier l'URL")
        copy_url_btn.clicked.connect(self.copy_url_to_clipboard)
        layout.addWidget(copy_url_btn)
        # Bouton Capture d'écran
        screenshot_btn = QPushButton("📸 Capture d'écran")
        screenshot_btn.clicked.connect(self.take_screenshot)
        layout.addWidget(screenshot_btn)
        # Bouton Scanner QR code
        qr_btn = QPushButton("🔎 Scanner QR code")
        qr_btn.clicked.connect(self.scan_qr_code)
        layout.addWidget(qr_btn)
        # Bouton Lecture vocale
        tts_btn = QPushButton("🔊 Lire la page")
        tts_btn.clicked.connect(self.read_page_text)
        layout.addWidget(tts_btn)
        # Bouton Extraire liens
        links_btn = QPushButton("🔗 Extraire liens")
        links_btn.clicked.connect(self.extract_links)
        layout.addWidget(links_btn)
        # Bouton Infos système
        system_info_btn = QPushButton("ℹ️ Infos système")
        system_info_btn.clicked.connect(self.show_system_info)
        layout.addWidget(system_info_btn)
        # Bouton Historique popup
        history_popup_btn = QPushButton("📜 Historique popup")
        history_popup_btn.clicked.connect(self.show_history_popup)
        layout.addWidget(history_popup_btn)
        
        # Bouton Console Live dans la sidebar
        log_btn = QPushButton("🖥️ Console Live")
        log_btn.clicked.connect(self.show_log_viewer)
        log_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                margin: 2px;
                border: 1px solid #6c757d;
                border-radius: 4px;
                background-color: #f8f9fa;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        layout.addWidget(log_btn)
        # Bouton Diagnostic dans la sidebar
        diag_btn = QPushButton("🩺 Diagnostic")
        diag_btn.clicked.connect(self.show_diagnostic)
        diag_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                margin: 2px;
                border: 1px solid #28a745;
                border-radius: 4px;
                background-color: #e3fcec;
                color: #218838;
            }
            QPushButton:hover {
                background-color: #c1e7d2;
            }
            QPushButton:pressed {
                background-color: #b3d9c2;
            }
        """)
        layout.addWidget(diag_btn)
        
        # Espaceur pour pousser les boutons vers le haut
        layout.addStretch()
        
        self.sidebar.setLayout(layout)
    
    def navigate_to_site(self, url):
        """Navigue vers un site spécifique."""
        self.browser.setUrl(QUrl(url))
        logging.info(f"Navigation vers : {url}")
    
    def toggle_sidebar(self):
        """Affiche ou masque la sidebar."""
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()
    
    def open_settings(self):
        """Ouvre la fenêtre de paramètres."""
        settings_dialog = SettingsDialog(self)
        settings_dialog.main_window = self  # Passe explicitement la référence
        result = settings_dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Ici on pourrait sauvegarder les paramètres
            logging.info("Paramètres sauvegardés")
        
        logging.info("Fenêtre de paramètres fermée")

    def navigate_home(self):
        """Action pour le bouton Accueil."""
        self.browser.setUrl(self.home_page_url)

    def navigate_to_url(self):
        """Navigue vers l'URL entrée dans la barre d'adresse."""
        q = QUrl(self.url_bar.text())
        if q.scheme() == "":
            q.setScheme("https")
        self.browser.setUrl(q)
        logging.info(f"Navigation vers : {q.toString()}")

    def closeEvent(self, event: QCloseEvent):
        logging.info("Fermeture de l'application")
        event.accept()


    def update_url_bar(self, q):
        """Met à jour la barre d'adresse avec l'URL actuelle."""
        self.url_bar.setText(q.toString())
        self.url_bar.setCursorPosition(0)

    def show_history(self):
        """Affiche une boîte de dialogue avec l'historique de navigation (version simple)"""
        from PyQt6.QtWidgets import QMessageBox
        # Pour l'instant, on affiche un message générique
        QMessageBox.information(self, "Historique", "Fonctionnalité d'historique à venir !")

    def check_and_update_files(self):
        from live_updater import LiveUpdateChecker, LiveFileDownloader
        self._checker = LiveUpdateChecker()
        self._checker.files_updated.connect(self.on_files_need_update)
        self._checker.no_update.connect(lambda: self._show_status_message("Tous les fichiers sont à jour.", 5000))
        self._checker.error_occurred.connect(lambda msg: self._show_status_message(f"Erreur MAJ : {msg}", 8000))
        self._checker.start()

    def show_notification(self, title, message, timeout=5):
        try:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=timeout)
        except Exception:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, title, message)

    # --- Callbacks critiques avec notifications ---
    def on_files_need_update(self, files):
        from live_updater import LiveFileDownloader
        self._downloader = LiveFileDownloader(files)
        self._downloader.download_finished.connect(lambda files: (self._show_status_message(f"Mise à jour appliquée : {', '.join(files)}", 8000), self.show_notification("Mise à jour", f"Fichiers mis à jour : {', '.join(files)}")))
        self._downloader.error_occurred.connect(lambda msg: (self._show_status_message(f"Erreur MAJ : {msg}", 8000), self.show_notification("Erreur MAJ", msg)))
        self._downloader.start()

    def _show_status_message(self, message: str, timeout: int = 5000):
        if hasattr(self, 'status') and self.status is not None:
            self.status.showMessage(message, timeout)

    def copy_url_to_clipboard(self):
        url = self.browser.url().toString()
        pyperclip.copy(url)
        self._show_status_message("URL copiée dans le presse-papiers !", 3000)
    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{now}.png"
        screenshot.save(filename)
        self._show_status_message(f"Capture d'écran enregistrée : {filename}", 5000)
    def scan_qr_code(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        file, _ = QFileDialog.getOpenFileName(self, "Sélectionner une image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            img = cv2.imread(file)
            decoded = decode_qr(img)
            if decoded:
                data = decoded[0].data.decode('utf-8')
                self._show_status_message(f"QR code détecté : {data}", 8000)
                self.browser.setUrl(QUrl(data))
            else:
                QMessageBox.warning(self, "QR code", "Aucun QR code détecté dans l'image.")
    def read_page_text(self):
        page = self.browser.page() if hasattr(self.browser, 'page') else None
        if page and hasattr(page, 'toPlainText'):
            page.toPlainText(lambda text: self._tts_speak(text))
        else:
            self._show_status_message("Impossible de lire le texte de la page.", 3000)
    def _tts_speak(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        self._show_status_message("Lecture vocale terminée.", 3000)
    def extract_links(self):
        def handle_html(html):
            try:
                soup = BeautifulSoup(html, 'html.parser')
                links = []
                for a in soup.find_all('a', href=True):
                    if isinstance(a, bs4.element.Tag):
                        href = a.get('href')
                        if isinstance(href, str):
                            links.append(href)
                from PyQt6.QtWidgets import QMessageBox
                msg = '\n'.join(links) if links else "Aucun lien trouvé."
                QMessageBox.information(self, "Liens de la page", msg)
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", f"Erreur lors de l'extraction des liens : {e}")
        page = self.browser.page() if hasattr(self.browser, 'page') else None
        if page and hasattr(page, 'toHtml'):
            page.toHtml(handle_html)
        else:
            self._show_status_message("Impossible d'extraire les liens de la page.", 3000)
    def show_system_info(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Infos système", f"CPU : {cpu}%\nRAM : {ram}%")
    def show_history_popup(self):
        try:
            import pandas as pd
            df = pd.read_json("update_history.json")
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
            dlg = QDialog(self)
            dlg.setWindowTitle("Historique des mises à jour")
            layout = QVBoxLayout()
            text = QTextEdit()
            text.setReadOnly(True)
            text.setText(df.to_string())
            layout.addWidget(text)
            dlg.setLayout(layout)
            dlg.exec()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"Impossible d'afficher l'historique : {e}")

    def refresh_status_indicators(self):
        # Connexion Internet
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            if getattr(self, '_last_conn_status', None) == False:
                self.show_notification("Connexion Internet", "Connexion rétablie.")
            self.status_conn.setText("🌐 Connexion : OK")
            self.status_conn.setStyleSheet("color: green;")
            self._last_conn_status = True
        except Exception:
            if getattr(self, '_last_conn_status', None) != False:
                self.show_notification("Connexion Internet", "Connexion perdue !")
            self.status_conn.setText("🌐 Connexion : HS")
            self.status_conn.setStyleSheet("color: red;")
            self._last_conn_status = False
        # Sync GitHub (on regarde le log de auto_sync)
        try:
            import os
            log_path = os.path.join(os.path.dirname(__file__), "auto_sync.log")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-10:]
                last = next((l for l in reversed(lines) if "Synchronisation terminée" in l), None)
                if last:
                    self.status_sync.setText("🔄 Sync : OK")
                    self.status_sync.setStyleSheet("color: green;")
                else:
                    self.status_sync.setText("🔄 Sync : ...")
                    self.status_sync.setStyleSheet("")
            else:
                self.status_sync.setText("🔄 Sync : ...")
                self.status_sync.setStyleSheet("")
        except Exception:
            self.status_sync.setText("🔄 Sync : ?")
            self.status_sync.setStyleSheet("color: orange;")
        # Notifications (on regarde si le port WebSocket est ouvert)
        try:
            import websocket
            ws = websocket.create_connection("ws://localhost:8000/ws", timeout=2)
            ws.close()
            self.status_notify.setText("🔔 Notif : OK")
            self.status_notify.setStyleSheet("color: green;")
        except Exception:
            self.status_notify.setText("🔔 Notif : HS")
            self.status_notify.setStyleSheet("color: red;")
        # Télémétrie (on regarde le log de telemetry_client)
        try:
            import os
            log_path = os.path.join(os.path.dirname(__file__), "telemetry.log")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-10:]
                last = next((l for l in reversed(lines) if "Télémétrie envoyée" in l), None)
                if last:
                    self.status_telemetry.setText("📡 Télémétrie : OK")
                    self.status_telemetry.setStyleSheet("color: green;")
                else:
                    self.status_telemetry.setText("📡 Télémétrie : ...")
                    self.status_telemetry.setStyleSheet("")
            else:
                self.status_telemetry.setText("📡 Télémétrie : ...")
                self.status_telemetry.setStyleSheet("")
        except Exception:
            self.status_telemetry.setText("📡 Télémétrie : ?")
            self.status_telemetry.setStyleSheet("color: orange;")

    def show_log_viewer(self):
        dlg = LogViewerDialog(self)
        dlg.exec()
    def show_diagnostic(self):
        from PyQt6.QtWidgets import QMessageBox
        report = get_status_report()
        QMessageBox.information(self, "État des services", report)


# --- Exécution de l'application ---
if __name__ == "__main__":
    console = Console()
    console.print("[bold green]Démarrage de Retrosoft...[/bold green]")
    import os
    import json
    import threading
    from config_watcher import start_config_watcher
    import signal
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    service_threads = {}
    service_procs = {}
    def start_auto_sync():
        import subprocess
        proc = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "auto_sync.py")],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        service_procs["auto_sync"] = proc
        logging.info("auto_sync lancé")
    def stop_auto_sync():
        proc = service_procs.get("auto_sync")
        if proc and proc.poll() is None:
            proc.terminate()
            logging.info("auto_sync arrêté")
    def start_telemetry():
        from telemetry_client import start_telemetry_client
        t = threading.Thread(target=start_telemetry_client, daemon=True)
        t.start()
        service_threads["telemetry"] = t
        logging.info("Télémétrie lancée")
    def stop_telemetry():
        # Pas d'arrêt propre, mais le thread s'arrêtera si désactivé dans la config
        logging.info("Télémétrie arrêt demandée (soft)")
    def start_notify():
        import subprocess
        notifier_path = os.path.join(os.path.dirname(__file__), "notifier_client.py")
        if os.path.exists(notifier_path):
            proc = subprocess.Popen([sys.executable, notifier_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            service_procs["notify"] = proc
            logging.info("Notifications temps réel lancées")
    def stop_notify():
        proc = service_procs.get("notify")
        if proc and proc.poll() is None:
            proc.terminate()
            logging.info("Notifications temps réel arrêtées")
    def apply_config(new, old):
        # Sync
        if new.get("sync_enabled", True) != old.get("sync_enabled", True):
            if new.get("sync_enabled", True):
                start_auto_sync()
            else:
                stop_auto_sync()
        # Télémétrie
        if new.get("telemetry_enabled", True) != old.get("telemetry_enabled", True):
            if new.get("telemetry_enabled", True):
                start_telemetry()
            else:
                stop_telemetry()
        # Notifications
        if new.get("notify_enabled", True) != old.get("notify_enabled", True):
            if new.get("notify_enabled", True):
                start_notify()
            else:
                stop_notify()
    # Charger la config avancée
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        config = {}
    # Lancer les services selon la config
    if config.get("sync_enabled", True):
        start_auto_sync()
    if config.get("telemetry_enabled", True):
        start_telemetry()
    if config.get("notify_enabled", True):
        start_notify()
    # Watcher de config pour rechargement à chaud
    start_config_watcher(apply_config)
    # Lancer la surveillance des services
    start_monitor()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        logging.info("Application en cours d'execution")
        sys.exit(app.exec())
    except Exception as e:
        logging.exception(f"Erreur non geree : {e}")
    finally:
        logging.info("Application terminee")
