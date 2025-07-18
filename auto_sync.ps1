# Script PowerShell pour synchronisation automatique
# À exécuter en arrière-plan pour synchroniser les changements

while ($true) {
    # Vérifier s'il y a des changements
    $status = git status --porcelain
    
    if ($status) {
        Write-Host "Changements détectés, synchronisation..."
        
        # Ajouter tous les fichiers modifiés
        git add .
        
        # Commit avec timestamp
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git commit -m "Auto-sync: $timestamp"
        
        # Push vers GitHub
        git push origin main
        
        Write-Host "Synchronisation terminée"
    }
    
    # Attendre 30 secondes avant la prochaine vérification
    Start-Sleep -Seconds 30
}