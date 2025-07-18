"""
Informations de version pour Retrosoft
"""

__version__ = "1.0.0"
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
    ]
}

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