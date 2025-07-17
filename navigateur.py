# /chemin/vers/votre/projet/mon_navigateur.py
import sys
import logging
import os
from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QStatusBar,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QAction, QCloseEvent

# Configuration basique du journal (enregistre dans un fichier)
logging.basicConfig(filename='browser_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Demarrage de l'application")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # --- Définir la page d'accueil locale ---
        logging.info("Definition de la page d'accueil")
        # On s'assure que le chemin est correct, peu importe d'où le script est lancé
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.home_page_url = QUrl.fromLocalFile(os.path.join(script_dir, "accueil.html"))

        # --- Fenêtre principale ---
        self.setWindowTitle("Navigateur Rapide")
        self.setWindowIcon(QIcon("icons/browser.svg")) # On utilise notre nouvelle icône SVG
        self.resize(1200, 800)

        logging.info("Creation de la vue web")
        # --- Vue Web ---
        self.browser = QWebEngineView()
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
        
        # --- Affichage ---
        self.setCentralWidget(self.browser)

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
