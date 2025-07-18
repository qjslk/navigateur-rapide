#!/usr/bin/env python3
"""
Système de mise à jour en temps réel pour Retrosoft
Télécharge automatiquement les fichiers Python modifiés depuis GitHub
"""

import requests
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import logging

class LiveUpdateChecker(QThread):
    """Thread pour vérifier les mises à jour de code en temps réel"""
    
    files_updated = pyqtSignal(list)  # Signal émis quand des fichiers sont mis à jour
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, current_version="1.0.0"):
        super().__init__()
        self.current_version = current_version
        self.github_repo = "qjslk/navigateur-rapide"
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}"
        self.files_to_monitor = [
            "navigateur.py",
            "version.py", 
            "updater.py",
            "accueil.html"
        ]
        
    def run(self):
        """Vérifier s'il y a des fichiers modifiés sur GitHub"""
        try:
            updated_files = []
            
            for filename in self.files_to_monitor:
                if self.check_file_updated(filename):
                    updated_files.append(filename)
            
            if updated_files:
                self.files_updated.emit(updated_files)
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.error_occurred.emit(f"Erreur de vérification: {str(e)}")
    
    def check_file_updated(self, filename):
        """Vérifier si un fichier spécifique a été modifié"""
        try:
            # Récupérer les informations du fichier depuis GitHub
            url = f"{self.github_api_url}/contents/{filename}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                github_data = response.json()
                github_sha = github_data["sha"]
                
                # Comparer avec le SHA local (si existe)
                local_sha_file = f".{filename}.sha"
                if os.path.exists(local_sha_file):
                    with open(local_sha_file, 'r') as f:
                        local_sha = f.read().strip()
                    
                    return github_sha != local_sha
                else:
                    # Première fois, considérer comme mise à jour
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de {filename}: {e}")
            return False

class LiveFileDownloader(QThread):
    """Thread pour télécharger les fichiers mis à jour"""
    
    download_finished = pyqtSignal(list)  # Liste des fichiers téléchargés
    error_occurred = pyqtSignal(str)
    
    def __init__(self, files_to_download):
        super().__init__()
        self.files_to_download = files_to_download
        self.github_repo = "qjslk/navigateur-rapide"
        self.github_raw_url = f"https://raw.githubusercontent.com/{self.github_repo}/main"
        
    def run(self):
        """Télécharger les fichiers mis à jour"""
        try:
            downloaded_files = []
            
            for filename in self.files_to_download:
                if self.download_file(filename):
                    downloaded_files.append(filename)
            
            if downloaded_files:
                self.download_finished.emit(downloaded_files)
            else:
                self.error_occurred.emit("Aucun fichier n'a pu être téléchargé")
                
        except Exception as e:
            self.error_occurred.emit(f"Erreur de téléchargement: {str(e)}")
    
    def download_file(self, filename):
        """Télécharger un fichier spécifique"""
        try:
            # URL du fichier brut sur GitHub
            file_url = f"{self.github_raw_url}/{filename}"
            response = requests.get(file_url, timeout=30)
            
            if response.status_code == 200:
                # Sauvegarder le fichier
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # Sauvegarder le SHA pour la prochaine vérification
                sha_url = f"https://api.github.com/repos/{self.github_repo}/contents/{filename}"
                sha_response = requests.get(sha_url, timeout=10)
                if sha_response.status_code == 200:
                    sha_data = sha_response.json()
                    with open(f".{filename}.sha", 'w') as f:
                        f.write(sha_data["sha"])
                
                logging.info(f"Fichier {filename} mis à jour avec succès")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Erreur lors du téléchargement de {filename}: {e}")
            return False

class LiveUpdater:
    """Gestionnaire principal des mises à jour en temps réel"""
    
    def __init__(self, parent_window, current_version="1.0.0"):
        self.parent = parent_window
        self.current_version = current_version
        self.checker = None
        self.downloader = None
        
        # Timer pour vérifications périodiques
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_for_updates_silent)
        
    def start_live_updates(self, interval_minutes=5):
        """Démarrer les mises à jour automatiques périodiques"""
        # Vérification initiale
        self.check_for_updates_silent()
        
        # Vérifications périodiques
        self.update_timer.start(interval_minutes * 60 * 1000)  # Convertir en millisecondes
        logging.info(f"Mises à jour automatiques activées (vérification toutes les {interval_minutes} minutes)")
    
    def stop_live_updates(self):
        """Arrêter les mises à jour automatiques"""
        self.update_timer.stop()
        logging.info("Mises à jour automatiques désactivées")
    
    def check_for_updates_silent(self):
        """Vérifier les mises à jour en mode silencieux"""
        if self.checker and self.checker.isRunning():
            return  # Une vérification est déjà en cours
            
        self.checker = LiveUpdateChecker(self.current_version)
        self.checker.files_updated.connect(self.on_files_updated)
        self.checker.no_update.connect(self.on_no_update_silent)
        self.checker.error_occurred.connect(self.on_error_silent)
        self.checker.start()
    
    def check_for_updates_manual(self):
        """Vérifier les mises à jour manuellement (avec messages)"""
        if self.checker and self.checker.isRunning():
            QMessageBox.information(
                self.parent,
                "Vérification en cours",
                "Une vérification de mise à jour est déjà en cours..."
            )
            return
            
        self.checker = LiveUpdateChecker(self.current_version)
        self.checker.files_updated.connect(self.on_files_updated_manual)
        self.checker.no_update.connect(self.on_no_update_manual)
        self.checker.error_occurred.connect(self.on_error_manual)
        self.checker.start()
    
    def on_files_updated(self, updated_files):
        """Fichiers mis à jour détectés (mode silencieux)"""
        self.download_updates(updated_files, silent=True)
    
    def on_files_updated_manual(self, updated_files):
        """Fichiers mis à jour détectés (mode manuel)"""
        reply = QMessageBox.question(
            self.parent,
            "Mises à jour disponibles",
            f"🔄 {len(updated_files)} fichier(s) mis à jour détecté(s):\n\n" +
            "\n".join([f"• {f}" for f in updated_files]) +
            "\n\nVoulez-vous télécharger et appliquer ces mises à jour?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.download_updates(updated_files, silent=False)
    
    def on_no_update_silent(self):
        """Aucune mise à jour (mode silencieux)"""
        logging.info("Aucune mise à jour disponible")
    
    def on_no_update_manual(self):
        """Aucune mise à jour (mode manuel)"""
        QMessageBox.information(
            self.parent,
            "Pas de mise à jour",
            "✅ Tous vos fichiers sont à jour!"
        )
    
    def on_error_silent(self, error_message):
        """Erreur de vérification (mode silencieux)"""
        logging.warning(f"Erreur de vérification des mises à jour: {error_message}")
    
    def on_error_manual(self, error_message):
        """Erreur de vérification (mode manuel)"""
        QMessageBox.warning(
            self.parent,
            "Erreur de vérification",
            f"❌ Impossible de vérifier les mises à jour:\n{error_message}"
        )
    
    def download_updates(self, files_to_update, silent=True):
        """Télécharger les mises à jour"""
        if self.downloader and self.downloader.isRunning():
            return  # Un téléchargement est déjà en cours
            
        self.downloader = LiveFileDownloader(files_to_update)
        self.downloader.download_finished.connect(
            lambda files: self.on_download_finished(files, silent)
        )
        self.downloader.error_occurred.connect(
            lambda error: self.on_download_error(error, silent)
        )
        self.downloader.start()
    
    def on_download_finished(self, downloaded_files, silent):
        """Téléchargement terminé"""
        if not silent:
            QMessageBox.information(
                self.parent,
                "Mise à jour terminée",
                f"✅ {len(downloaded_files)} fichier(s) mis à jour:\n\n" +
                "\n".join([f"• {f}" for f in downloaded_files]) +
                "\n\n🔄 Redémarrez l'application pour appliquer les changements."
            )
        else:
            # Notification discrète dans les logs
            logging.info(f"Mise à jour automatique: {len(downloaded_files)} fichier(s) mis à jour")
            
            # Optionnel: notification système
            if hasattr(self.parent, 'show_notification'):
                self.parent.show_notification(
                    "Retrosoft mis à jour",
                    f"{len(downloaded_files)} fichier(s) mis à jour automatiquement"
                )
    
    def on_download_error(self, error_message, silent):
        """Erreur de téléchargement"""
        if not silent:
            QMessageBox.critical(
                self.parent,
                "Erreur de mise à jour",
                f"❌ Erreur lors de la mise à jour:\n{error_message}"
            )
        else:
            logging.error(f"Erreur de mise à jour automatique: {error_message}")

# Fonction utilitaire pour intégrer facilement dans l'application principale
def setup_live_updater(main_window, version="1.0.0", auto_check_minutes=5):
    """Configure le système de mise à jour en temps réel"""
    updater = LiveUpdater(main_window, version)
    
    # Démarrer les mises à jour automatiques
    updater.start_live_updates(auto_check_minutes)
    
    return updater