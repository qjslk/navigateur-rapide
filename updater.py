#!/usr/bin/env python3
"""
Système de mise à jour automatique pour Retrosoft
Vérifie les nouvelles versions sur GitHub et les télécharge automatiquement
"""

import requests
import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt

class UpdateChecker(QThread):
    """Thread pour vérifier les mises à jour sans bloquer l'interface"""
    
    update_available = pyqtSignal(dict)  # Signal émis quand une MAJ est disponible
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, current_version="1.0.0"):
        super().__init__()
        self.current_version = current_version
        self.github_repo = "qjslk/navigateur-rapide"
        
    def run(self):
        """Vérifier s'il y a une nouvelle version sur GitHub"""
        try:
            # API GitHub pour récupérer la dernière release
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                
                if self.is_newer_version(latest_version, self.current_version):
                    self.update_available.emit(release_data)
                else:
                    self.no_update.emit()
            else:
                self.error_occurred.emit(f"Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            self.error_occurred.emit(f"Erreur de connexion: {str(e)}")
    
    def is_newer_version(self, latest, current):
        """Compare les versions (format: x.y.z)"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Égaliser les longueurs
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            
            return latest_parts > current_parts
        except:
            return False

class UpdateDownloader(QThread):
    """Thread pour télécharger et installer la mise à jour"""
    
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, download_url, filename):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        
    def run(self):
        """Télécharger la mise à jour"""
        try:
            response = requests.get(self.download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, self.filename)
            
            with open(file_path, 'wb') as file:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress_updated.emit(progress)
            
            self.download_finished.emit(file_path)
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur de téléchargement: {str(e)}")

class AutoUpdater:
    """Gestionnaire principal des mises à jour automatiques"""
    
    def __init__(self, parent_window, current_version="1.0.0"):
        self.parent = parent_window
        self.current_version = current_version
        self.checker = None
        self.downloader = None
        
    def check_for_updates(self, silent=False):
        """Vérifier les mises à jour (silent=True pour vérification automatique)"""
        self.silent_check = silent
        
        self.checker = UpdateChecker(self.current_version)
        self.checker.update_available.connect(self.on_update_available)
        self.checker.no_update.connect(self.on_no_update)
        self.checker.error_occurred.connect(self.on_error)
        self.checker.start()
    
    def on_update_available(self, release_data):
        """Nouvelle version disponible"""
        version = release_data["tag_name"]
        description = release_data["body"][:200] + "..." if len(release_data["body"]) > 200 else release_data["body"]
        
        # Chercher l'asset .exe dans la release
        exe_asset = None
        for asset in release_data.get("assets", []):
            if asset["name"].endswith(".exe"):
                exe_asset = asset
                break
        
        if not exe_asset:
            if not self.silent_check:
                QMessageBox.information(
                    self.parent,
                    "Mise à jour disponible",
                    f"Version {version} disponible, mais aucun exécutable trouvé.\n\nVeuillez télécharger manuellement depuis GitHub."
                )
            return
        
        # Demander à l'utilisateur s'il veut mettre à jour
        reply = QMessageBox.question(
            self.parent,
            "Mise à jour disponible",
            f"🎉 Nouvelle version disponible: {version}\n\n"
            f"📝 Nouveautés:\n{description}\n\n"
            f"Voulez-vous télécharger et installer cette mise à jour?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.download_update(exe_asset["browser_download_url"], exe_asset["name"])
    
    def on_no_update(self):
        """Aucune mise à jour disponible"""
        if not self.silent_check:
            QMessageBox.information(
                self.parent,
                "Pas de mise à jour",
                "Vous utilisez déjà la dernière version de Retrosoft! 🎉"
            )
    
    def on_error(self, error_message):
        """Erreur lors de la vérification"""
        if not self.silent_check:
            QMessageBox.warning(
                self.parent,
                "Erreur de mise à jour",
                f"Impossible de vérifier les mises à jour:\n{error_message}"
            )
    
    def download_update(self, download_url, filename):
        """Télécharger la mise à jour"""
        # Dialogue de progression
        self.progress_dialog = QProgressDialog(
            "Téléchargement de la mise à jour...",
            "Annuler",
            0, 100,
            self.parent
        )
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        # Démarrer le téléchargement
        self.downloader = UpdateDownloader(download_url, filename)
        self.downloader.progress_updated.connect(self.progress_dialog.setValue)
        self.downloader.download_finished.connect(self.on_download_finished)
        self.downloader.error_occurred.connect(self.on_download_error)
        self.progress_dialog.canceled.connect(self.downloader.terminate)
        self.downloader.start()
    
    def on_download_finished(self, file_path):
        """Téléchargement terminé"""
        self.progress_dialog.close()
        
        reply = QMessageBox.question(
            self.parent,
            "Mise à jour téléchargée",
            f"✅ Mise à jour téléchargée avec succès!\n\n"
            f"📁 Emplacement: {file_path}\n\n"
            f"Voulez-vous installer maintenant?\n"
            f"(Retrosoft se fermera automatiquement)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.install_update(file_path)
    
    def on_download_error(self, error_message):
        """Erreur de téléchargement"""
        self.progress_dialog.close()
        QMessageBox.critical(
            self.parent,
            "Erreur de téléchargement",
            f"❌ Échec du téléchargement:\n{error_message}"
        )
    
    def install_update(self, file_path):
        """Installer la mise à jour"""
        try:
            # Lancer l'installateur et fermer l'application actuelle
            subprocess.Popen([file_path])
            sys.exit(0)
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Erreur d'installation",
                f"❌ Impossible de lancer l'installateur:\n{str(e)}\n\n"
                f"Veuillez lancer manuellement: {file_path}"
            )

# Fonction utilitaire pour intégrer facilement dans l'application principale
def setup_auto_updater(main_window, version="1.0.0"):
    """Configure le système de mise à jour pour l'application principale"""
    updater = AutoUpdater(main_window, version)
    
    # Vérification automatique au démarrage (silencieuse)
    updater.check_for_updates(silent=True)
    
    return updater