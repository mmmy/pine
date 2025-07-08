@echo off
color 0B
echo ========================================
echo    Pine Script Strategy Generator
echo ========================================
echo.
echo This will generate a Pine Script strategy from your CSV data.
echo.
echo Files needed:
echo  - trading_orders.csv
echo  - scheduled_trading_strategy.template
echo.
echo Output files:
echo  - generated_strategy.pine
echo  - ../scheduled_trading_strategy_final.pine
echo.
echo Starting generator...
echo.

powershell.exe -ExecutionPolicy Bypass -File "generate_strategy.ps1"

echo.
if %ERRORLEVEL% EQU 0 (
  echo Success! Your strategy has been generated.
  echo The file content has been copied to clipboard.
) else (
  echo There was an error generating the strategy.
  echo Please check the error messages above.
)
echo.
echo Press any key to exit...
pause >nul
