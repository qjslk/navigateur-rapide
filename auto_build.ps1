# Script de build automatique
# Surveille les changements et rebuild l'application

Write-Host "🚀 Surveillance automatique activée..."
Write-Host "Appuyez sur Ctrl+C pour arrêter"

# Fonction de build (utilise un verbe approuvé)
function Invoke-AppBuild {
    Write-Host "🔨 Reconstruction de l'application..."
    
    # Nettoyer les anciens builds
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    
    # Rebuild avec PyInstaller
    python -m PyInstaller "Navigateur Rapide.spec" --clean
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Build réussi!"
        
        # Créer l'installateur si Inno Setup est disponible
        if (Get-Command "iscc" -ErrorAction SilentlyContinue) {
            Write-Host "📦 Création de l'installateur..."
            iscc "create_installer.iss"
            Write-Host "✅ Installateur créé!"
        }
    } else {
        Write-Host "❌ Erreur lors du build"
    }
}

# Build initial
Invoke-AppBuild

# Surveillance des fichiers
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = Get-Location
$watcher.Filter = "*.py"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

# Action lors d'un changement
$action = {
    $name = $Event.SourceEventArgs.Name
    
    Write-Host "📝 Fichier modifié: $name"
    Start-Sleep -Seconds 2  # Attendre que l'écriture soit terminée
    Invoke-AppBuild
}

# Enregistrer les événements
Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action

try {
    # Boucle infinie
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # Nettoyage
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
}