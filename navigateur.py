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
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QAction, QCloseEvent
from updater import setup_auto_updater
from live_updater import setup_live_updater
from version import get_version, get_app_info

# Configuration basique du journal (enregistre dans un fichier)
logging.basicConfig(filename='browser_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Demarrage de l'application")


class SettingsDialog(QDialog):
    """Fenêtre de paramètres pour Retrosoft"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Paramètres - Retrosoft")
        self.setFixedSize(500, 400)
        self.setWindowIcon(QIcon("icons/browser.svg"))
        
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
        
        # Onglet À propos
        about_tab = self.create_about_tab()
        tabs.addTab(about_tab, "ℹ️ À propos")
        
        layout.addWidget(tabs)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
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
        if hasattr(self.parent(), 'updater'):
            self.parent().updater.check_for_updates(silent=False)
    
    def check_live_updates_now(self):
        """Vérifie les mises à jour de code en temps réel"""
        if hasattr(self.parent(), 'live_updater'):
            self.parent().live_updater.check_for_updates_manual()
    
    def open_url(self, url):
        """Ouvre une URL dans le navigateur parent"""
        if hasattr(self.parent(), 'browser'):
            self.parent().browser.setUrl(QUrl(url))
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


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # --- Définir la page d'accueil locale ---
        logging.info("Definition de la page d'accueil")
        # On s'assure que le chemin est correct, peu importe d'où le script est lancé
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.home_page_url = QUrl.fromLocalFile(os.path.join(script_dir, "accueil.html"))

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
        self.setStatusBar(QStatusBar(self))
        
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


# --- Exécution de l'application ---
if __name__ == "__main__":
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
