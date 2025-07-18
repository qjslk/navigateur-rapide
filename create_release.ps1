# Script pour créer une release GitHub avec l'exécutable
param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Description = "Nouvelle version de Retrosoft"
)

Write-Host "🚀 Création d'une release GitHub v$Version"

# 1. Build de l'application
Write-Host "🔨 Build de l'application..."
pyinstaller --onefile --windowed --name "Retrosoft-v$Version" --icon="icons/browser.ico" navigateur.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du build"
    exit 1
}

# 2. Vérifier que l'exécutable existe
$exePath = "dist/Retrosoft-v$Version.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "❌ Exécutable non trouvé: $exePath"
    exit 1
}

Write-Host "✅ Exécutable créé: $exePath"

# 3. Commit et tag
Write-Host "📝 Création du tag Git..."
git add .
git commit -m "Release v$Version"
git tag -a "v$Version" -m "Version $Version"
git push origin main
git push origin "v$Version"

Write-Host "✅ Tag v$Version créé et poussé"

# 4. Instructions pour créer la release sur GitHub
Write-Host ""
Write-Host "🎯 Étapes suivantes:"
Write-Host "1. Allez sur: https://github.com/qjslk/navigateur-rapide/releases/new"
Write-Host "2. Tag version: v$Version"
Write-Host "3. Release title: Retrosoft v$Version"
Write-Host "4. Description: $Description"
Write-Host "5. Uploadez le fichier: $exePath"
Write-Host "6. Cliquez sur 'Publish release'"
Write-Host ""
Write-Host "📁 Fichier à uploader: $(Resolve-Path $exePath)"

# 5. Ouvrir le navigateur sur la page de création de release
Start-Process "https://github.com/qjslk/navigateur-rapide/releases/new"

Write-Host "🎉 Release préparée! Suivez les instructions ci-dessus."