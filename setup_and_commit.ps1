# Setup git and commit Pine Script Strategy Generator

Write-Host "Setting up git and committing code..." -ForegroundColor Cyan

# Configure git user (if not already configured)
git config --global user.name "Pine Script Generator"
git config --global user.email "pine@generator.local"

# Initialize git if needed
if (-not (Test-Path ".git")) {
    git init
}

# Add all files
git add .

# Commit
git commit -m "feat: Pine Script Strategy Generator with timezone handling

- PowerShell script converts CSV trading data to Pine Script
- Automatic timezone handling (+08:00 default)
- Multiple time format support
- Complete Chinese documentation
- Batch launchers for easy use
- Template-based generation
- Clipboard integration"

Write-Host "Code committed successfully!" -ForegroundColor Green
