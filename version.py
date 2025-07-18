"""
Informations de version pour Retrosoft
"""

import os
import json
from PyQt6.QtWidgets import QInputDialog, QApplication

__version__ = "2.0.0"
__app_name__ = "Retrosoft"
__description__ = "Navigateur web rapide avec sidebar et mise à jour automatique"
__author__ = "Votre nom"
__github_repo__ = "qjslk/navigateur-rapide"

# Historique des versions
VERSION_HISTORY = {
    "1.0.0": [
        "🎉 Version initiale de Retrosoft",
        "🔧 Navigateur web basé sur PyQt6",
        "📱 Sidebar avec raccourcis rapides",
        "🔄 Système de mise à jour automatique",
        "🏠 Page d'accueil personnalisée"
    ],
    "1.1.0": [
        "⚙️ Ajout du bouton Paramètres dans la sidebar",
        "🎨 Fenêtre de paramètres avec onglets (Général, Mise à jour, À propos)",
        "🔧 Configuration de la page d'accueil et moteur de recherche",
        "📋 Informations détaillées sur l'application",
        "🔍 Bouton 'Vérifier maintenant' pour les mises à jour"
    ],
    "1.2.0": [
        "🌐 Bouton 'Définir comme navigateur par défaut' dans les paramètres",
        "📝 Enregistrement automatique de Retrosoft comme navigateur web",
        "🔗 Support des URLs passées en argument (liens externes)",
        "✅ Statut du navigateur par défaut affiché en temps réel",
        "🖥️ Nouveau groupe 'Système' dans les paramètres"
    ],
    "2.0.0": [
        "🚀 Synchronisation dynamique avec n'importe quel dépôt GitHub public",
        "🔔 Mises à jour automatiques en temps réel via WebSocket",
        "🛡️ Plus besoin de clé API, sécurité renforcée",
        "🖥️ Fenêtre de configuration du dépôt au premier lancement",
        "⚡ Robustesse et rapidité accrues"
    ]
}

CONFIG_FILE = "config.json"
DEFAULT_REPO = "https://github.com/qjslk/navigateur-rapide"

def get_version():
    """Retourne la version actuelle"""
    return __version__

def get_app_info():
    """Retourne les informations complètes de l'application"""
    return {
        "name": __app_name__,
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "repo": __github_repo__
    }

def get_github_repo_url():
    """Retourne l'URL du dépôt GitHub à utiliser (demande à l'utilisateur au premier lancement)"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("github_repo", DEFAULT_REPO)
    # Demande à l'utilisateur au premier lancement
    app = QApplication.instance() or QApplication([])
    repo_url, ok = QInputDialog.getText(
        None,
        "Configuration du dépôt GitHub",
        "Entrez l'URL du dépôt GitHub à synchroniser :",
        text=DEFAULT_REPO
    )
    if ok and repo_url:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"github_repo": repo_url}, f)
        return repo_url
    else:
        return DEFAULT_REPO