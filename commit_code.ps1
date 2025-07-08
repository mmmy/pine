# Git commit script for Pine Script Strategy Generator

Write-Host "Pine Script Strategy Generator - Git Commit" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
}

# Check git status
Write-Host "Checking git status..." -ForegroundColor Yellow
git status

# Add all files
Write-Host "Adding files to git..." -ForegroundColor Yellow
git add .

# Show what will be committed
Write-Host "Files to be committed:" -ForegroundColor Yellow
git status --cached

# Commit with a descriptive message
$commitMessage = "feat: Add Pine Script Strategy Generator with timezone handling

Features:
- PowerShell script to convert CSV trading data to Pine Script
- Automatic timezone handling (adds +08:00 if missing)
- Support for multiple time formats (YYYY-MM-DD HH:MM:SS, YYYY/M/D HH:MM)
- Comprehensive Chinese documentation
- Batch files for easy execution
- Template-based strategy generation
- Automatic clipboard copy functionality

Files added:
- schedule/generate_strategy.ps1 - Main generator script
- schedule/copy_strategy_to_clipboard.ps1 - Clipboard utility
- schedule/run_generator.bat - English batch launcher
- schedule/运行策略生成器.bat - Chinese batch launcher
- schedule/trading_orders.csv - Sample trading data
- schedule/scheduled_trading_strategy.template - Pine Script template
- schedule/README.md - Complete user guide (Chinese)
- schedule/QUICK_START.md - Quick start guide (Chinese)
- schedule/使用教程.md - Detailed tutorial (Chinese)
- schedule/故障排除.md - Troubleshooting guide (Chinese)
- schedule/文档索引.md - Documentation index (Chinese)
- .gitignore - Git ignore rules"

Write-Host "Committing with message:" -ForegroundColor Yellow
Write-Host $commitMessage -ForegroundColor White

git commit -m $commitMessage

Write-Host ""
Write-Host "Git commit completed!" -ForegroundColor Green
Write-Host "Repository status:" -ForegroundColor Yellow
git status
