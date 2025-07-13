$PSDefaultParameterValues = @{'*:Encoding' = 'utf8'}

# PowerShell Script: Replace trading_orders.csv data into scheduled_trading_strategy.template
# Function: Read CSV trading data, replace template placeholders, generate Pine Script strategy file and copy to clipboard
# Date: 2025-07-08

# Set file paths
$CsvPath = "trading_orders.csv"
$TemplatePath = "scheduled_trading_strategy.template"
$OutputPath = "generated_strategy.pine"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Pine Script Strategy Generator" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "CSV file: $CsvPath" -ForegroundColor Yellow
Write-Host "Template file: $TemplatePath" -ForegroundColor Yellow
Write-Host "Output file: $OutputPath" -ForegroundColor Yellow
Write-Host ""

# Step 1: Delete old generated files
Write-Host "Step 1: Cleaning up old generated files..." -ForegroundColor Yellow

if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Force
    Write-Host "✓ Deleted old file: $OutputPath" -ForegroundColor Green
} else {
    Write-Host "✓ No old file to delete: $OutputPath" -ForegroundColor Green
}

Write-Host ""

# Get timezone input from user
Write-Host "Timezone Configuration:" -ForegroundColor Yellow
$timezoneInput = Read-Host "Enter timezone offset (default is 8 for GMT+8, press Enter for default)"
if ([string]::IsNullOrEmpty($timezoneInput)) {
    $timezone = 8
} else {
    try {
        $timezone = [int]$timezoneInput
        if ($timezone -lt -12 -or $timezone -gt 14) {
            Write-Host "Error: Timezone must be between -12 and +14" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "Error: Invalid timezone input, please enter a number" -ForegroundColor Red
        exit 1
    }
}
$timezoneStr = if ($timezone -ge 0) { "+{0:D2}:00" -f $timezone } else { "-{0:D2}:00" -f [Math]::Abs($timezone) }
$timezoneGMT = if ($timezone -ge 0) { "GMT+$timezone" } else { "GMT$timezone" }
Write-Host "✓ Using timezone: $timezoneGMT ($timezoneStr)" -ForegroundColor Green

Write-Host ""

# Check if input files exist
Write-Host "Step 2: Checking input files..." -ForegroundColor Yellow

if (-not (Test-Path $CsvPath)) {
    Write-Host "Error: CSV file not found - $CsvPath" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✓ CSV file found: $CsvPath" -ForegroundColor Green
}

if (-not (Test-Path $TemplatePath)) {
    Write-Host "Error: Template file not found - $TemplatePath" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✓ Template file found: $TemplatePath" -ForegroundColor Green
}

Write-Host ""

try {
    Write-Host "Step 3: Processing CSV data..." -ForegroundColor Yellow

    # Read CSV file content (skip header row)
    $csvLines = Get-Content $CsvPath -Encoding UTF8
    $dataLines = $csvLines[1..($csvLines.Length-1)]  # Skip first row header

    Write-Host "✓ Found $($dataLines.Count) trading records" -ForegroundColor Green

    # Generate Pine Script code
    $pineScriptLines = @()

    foreach ($line in $dataLines) {
        if ($line.Trim() -ne "") {
            $parts = $line.Split(',')
            $time = $parts[0].Trim()
            $direction = $parts[1].Trim()
            $quantity = $parts[2].Trim()

            # Handle different time formats and timezone conversion
            # Normalize date format: convert "2025/7/9 16:45" to "2025-07-09 16:45:00"
            if ($time -match '(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})') {
                $year = $matches[1]
                $month = $matches[2].PadLeft(2, '0')
                $day = $matches[3].PadLeft(2, '0')
                $hour = $matches[4].PadLeft(2, '0')
                $minute = $matches[5]
                $time = "$year-$month-$day $hour`:$minute`:00"
                Write-Host "  ℹ Normalized time format to: $time" -ForegroundColor Cyan
            }

            # If no timezone info, add user specified timezone
            if ($time -notmatch '\+\d{2}:\d{2}$') {
                $time = $time + $timezoneStr
                Write-Host "  ℹ Added timezone $timezoneStr to: $time" -ForegroundColor Cyan
            }

            # Convert time format: from "2025-07-08 09:30:00+08:00" to "2025-07-08 09:30:00 GMT+8"
            # Handle different timezone formats
            $timeFormatted = $time -replace '[\+\-]\d{2}:\d{2}', " $timezoneGMT"

            # Generate Pine Script code - use original Chinese direction
            $pineScriptLines += "    // Trading time: $time, Direction: $direction, Quantity: $quantity"
            $pineScriptLines += "    array.push(tradeTimes, timestamp(`"$timeFormatted`"))"
            $pineScriptLines += "    array.push(tradeSignals, `"$direction`")"
            $pineScriptLines += "    array.push(tradeSizes, $quantity.0)"
            $pineScriptLines += ""
        }
    }

    Write-Host ""
    Write-Host "Step 4: Generating Pine Script code..." -ForegroundColor Yellow

    # Convert array to string
    $replacementText = $pineScriptLines -join "`n"

    # Read template file
    $templateContent = Get-Content $TemplatePath -Raw -Encoding UTF8

    # Replace {{template}} placeholder
    $finalContent = $templateContent -replace '\{\{template\}\}', $replacementText

    # Write to new file
    $finalContent | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Host "✓ Generated file: $OutputPath" -ForegroundColor Green

    Write-Host ""
    Write-Host "Step 5: Copying to clipboard..." -ForegroundColor Yellow

    # Copy content to clipboard
    $finalContent | Set-Clipboard
    Write-Host "✓ Content copied to clipboard" -ForegroundColor Green

    # Show success information
    Write-Host ""
    Write-Host "Step 5: Summary" -ForegroundColor Yellow
    Write-Host "✓ Strategy file generated: $OutputPath" -ForegroundColor Green
    Write-Host "✓ Content copied to clipboard" -ForegroundColor Green
    Write-Host "✓ Processed $($dataLines.Count) trading records" -ForegroundColor Green

    # Show file information
    if (Test-Path $OutputPath) {
        $fileInfo = Get-Item $OutputPath
        Write-Host "✓ File size: $($fileInfo.Length) bytes" -ForegroundColor Green
    } else {
        Write-Host "⚠ Warning: Output file not found after generation" -ForegroundColor Yellow
    }

    # Show generated trading plan summary
    Write-Host ""
    Write-Host "Generated Trading Plan Summary:" -ForegroundColor Cyan
    Write-Host ("=" * 50) -ForegroundColor Cyan

    foreach ($line in $dataLines) {
        if ($line.Trim() -ne "") {
            $parts = $line.Split(',')
            $time = $parts[0].Trim()
            $direction = $parts[1].Trim()
            $quantity = $parts[2].Trim()
            $directionText = ""
            $emoji = ""
            
            # Clean direction text of any hidden characters
            $direction = $direction.Trim().Replace("`r", "").Replace("`n", "")
            
            switch ($direction) {
                "做多" { $directionText = "Long"; $emoji = "📈" }
                "平多" { $directionText = "Close Long"; $emoji = "📉" }
                "做空" { $directionText = "Short"; $emoji = "📉" }
                "平空" { $directionText = "Close Short"; $emoji = "📈" }
                default { 
                    $directionText = "Unknown ($direction)"; 
                    $emoji = "?" 
                    Write-Host "  ⚠ Unknown direction: '$direction' (length: $($direction.Length))" -ForegroundColor Yellow
                }
            }
            
            Write-Host "$emoji $time - $directionText $quantity shares" -ForegroundColor White
        }
    }

    Write-Host ("=" * 50) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Task completed! File generated and copied to clipboard!" -ForegroundColor Green
    Write-Host "You can now paste it directly into TradingView." -ForegroundColor Yellow

} catch {
    Write-Host ""
    Write-Host "Error occurred: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check file format and permissions." -ForegroundColor Yellow
    exit 1
}