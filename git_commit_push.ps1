# Git commit and push script

Write-Host "Git Commit & Push Script" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Cyan

# Check git status
Write-Host "Checking git status..." -ForegroundColor Yellow
git status

# Add all changes
Write-Host "Adding all changes..." -ForegroundColor Yellow
git add .

# Check what will be committed
Write-Host "Files to be committed:" -ForegroundColor Yellow
git status --cached

# Commit changes
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "docs: Update MT5 requirements and add flowcharts

- Updated MT5 requirements document with enhanced specifications
- Added comprehensive flowcharts for Pine Script strategy generator
- Included system architecture, data processing, and execution flow diagrams
- Enhanced documentation with visual representations of the system"

# Push to remote
Write-Host "Pushing to remote repository..." -ForegroundColor Yellow
git push origin master

Write-Host "Git operations completed!" -ForegroundColor Green
