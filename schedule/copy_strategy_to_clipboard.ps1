# Copy generated strategy to clipboard
$content = Get-Content "generated_strategy.pine" -Raw -Encoding UTF8
$content | Set-Clipboard
Write-Host "Strategy file content copied to clipboard successfully!" -ForegroundColor Green
Write-Host "File: generated_strategy.pine" -ForegroundColor Yellow
Write-Host "You can now paste it into TradingView." -ForegroundColor Cyan
