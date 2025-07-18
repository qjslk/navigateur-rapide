"""
Script pour enregistrer Retrosoft comme navigateur dans Windows
"""
import winreg
import os
import sys

def register_browser():
    """Enregistre Retrosoft comme navigateur dans le registre Windows"""
    
    # Chemin vers l'exécutable
    if getattr(sys, 'frozen', False):
        # Si l'application est compilée avec PyInstaller
        exe_path = sys.executable
    else:
        # Si on exécute le script Python
        exe_path = os.path.abspath(sys.argv[0])
    
    app_name = "Retrosoft"
    app_description = "Navigateur web rapide et moderne"
    
    try:
        # 1. Enregistrer l'application
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\{app_name}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, app_description)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, exe_path)
        
        # 2. Enregistrer comme navigateur web
        prog_id = f"{app_name}.HTML"
        
        # Créer ProgID
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{app_name} HTML Document")
            winreg.SetValueEx(key, "FriendlyTypeName", 0, winreg.REG_SZ, f"{app_name} HTML Document")
        
        # Commande pour ouvrir
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\shell\\open\\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        
        # 3. Enregistrer pour les protocoles HTTP et HTTPS
        for protocol in ["http", "https"]:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{protocol}\\shell\\open\\command") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        
        # 4. Enregistrer dans la liste des navigateurs disponibles
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, app_name)
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}\\Capabilities") as key:
            winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, app_name)
            winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ, app_description)
        
        # Associations de fichiers
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}\\Capabilities\\FileAssociations") as key:
            winreg.SetValueEx(key, ".html", 0, winreg.REG_SZ, prog_id)
            winreg.SetValueEx(key, ".htm", 0, winreg.REG_SZ, prog_id)
        
        # Associations d'URL
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}\\Capabilities\\URLAssociations") as key:
            winreg.SetValueEx(key, "http", 0, winreg.REG_SZ, prog_id)
            winreg.SetValueEx(key, "https", 0, winreg.REG_SZ, prog_id)
        
        # Commande par défaut
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Clients\\StartMenuInternet\\{app_name}\\shell\\open\\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{exe_path}"')
        
        print(f"✅ {app_name} a été enregistré comme navigateur web !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement : {e}")
        return False

if __name__ == "__main__":
    register_browser()