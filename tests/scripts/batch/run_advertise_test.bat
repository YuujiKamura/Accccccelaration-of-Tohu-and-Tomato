@echo off
REM アドバタイズモードテスト実行バッチファイル
REM 高度なテストフレームワークを使用してアドバタイズモードをテスト・分析・改善します

echo ===================================
echo アドバタイズモードテストフレームワーク
echo ===================================

:menu
echo.
echo 実行するオプションを選択してください:
echo 1. 単体テスト実行 (推奨: 最初にこれを実行)
echo 2. 統合テスト実行
echo 3. アドバタイズモード分析実行 (詳細な分析)
echo 4. ベンチマークテスト実行 (改善前後の比較)
echo 5. 全テスト実行 (長時間かかります)
echo 6. クイックテスト (高速実行モード)
echo 7. 終了
echo.

set /p choice=選択 (1-7): 

if "%choice%"=="1" goto unit_tests
if "%choice%"=="2" goto integration_tests
if "%choice%"=="3" goto analyzer
if "%choice%"=="4" goto benchmark
if "%choice%"=="5" goto all_tests
if "%choice%"=="6" goto quick_tests
if "%choice%"=="7" goto end

echo 無効な選択です。もう一度お試しください。
goto menu

:unit_tests
echo.
echo 単体テスト実行中...
echo -----------------------------------
python -m unittest discover -s tests/unit_tests -p test_*.py
echo.
echo 単体テスト完了
pause
goto menu

:integration_tests
echo.
echo 統合テスト実行中...
echo -----------------------------------
python tests/integration_tests/run_tests.py
echo.
echo 統合テスト完了
pause
goto menu

:analyzer
echo.
echo アドバタイズモード分析実行中...
echo -----------------------------------
python test_advertise_mode.py
echo.
echo 分析完了
pause
goto menu

:benchmark
echo.
echo ベンチマークテスト実行中...
echo -----------------------------------
python tests/integration_tests/run_tests.py --benchmark
echo.
echo ベンチマーク完了
pause
goto menu

:all_tests
echo.
echo 全テスト実行中 (長時間かかります)...
echo -----------------------------------
echo 1. 単体テスト
python -m unittest discover -s tests/unit_tests -p test_*.py
echo.
echo 2. 統合テスト
python tests/integration_tests/run_tests.py
echo.
echo 3. ベンチマークテスト
python tests/integration_tests/run_tests.py --benchmark
echo.
echo 全テスト完了
pause
goto menu

:quick_tests
echo.
echo クイックテスト実行中...
echo -----------------------------------
python tests/integration_tests/run_tests.py --quick
echo.
echo クイックテスト完了
pause
goto menu

:end
echo.
echo テストフレームワークを終了します
exit /b 0 
REM アドバタイズモードテスト実行バッチファイル
REM 高度なテストフレームワークを使用してアドバタイズモードをテスト・分析・改善します

echo ===================================
echo アドバタイズモードテストフレームワーク
echo ===================================

:menu
echo.
echo 実行するオプションを選択してください:
echo 1. 単体テスト実行 (推奨: 最初にこれを実行)
echo 2. 統合テスト実行
echo 3. アドバタイズモード分析実行 (詳細な分析)
echo 4. ベンチマークテスト実行 (改善前後の比較)
echo 5. 全テスト実行 (長時間かかります)
echo 6. クイックテスト (高速実行モード)
echo 7. 終了
echo.

set /p choice=選択 (1-7): 

if "%choice%"=="1" goto unit_tests
if "%choice%"=="2" goto integration_tests
if "%choice%"=="3" goto analyzer
if "%choice%"=="4" goto benchmark
if "%choice%"=="5" goto all_tests
if "%choice%"=="6" goto quick_tests
if "%choice%"=="7" goto end

echo 無効な選択です。もう一度お試しください。
goto menu

:unit_tests
echo.
echo 単体テスト実行中...
echo -----------------------------------
python -m unittest discover -s tests/unit_tests -p test_*.py
echo.
echo 単体テスト完了
pause
goto menu

:integration_tests
echo.
echo 統合テスト実行中...
echo -----------------------------------
python tests/integration_tests/run_tests.py
echo.
echo 統合テスト完了
pause
goto menu

:analyzer
echo.
echo アドバタイズモード分析実行中...
echo -----------------------------------
python test_advertise_mode.py
echo.
echo 分析完了
pause
goto menu

:benchmark
echo.
echo ベンチマークテスト実行中...
echo -----------------------------------
python tests/integration_tests/run_tests.py --benchmark
echo.
echo ベンチマーク完了
pause
goto menu

:all_tests
echo.
echo 全テスト実行中 (長時間かかります)...
echo -----------------------------------
echo 1. 単体テスト
python -m unittest discover -s tests/unit_tests -p test_*.py
echo.
echo 2. 統合テスト
python tests/integration_tests/run_tests.py
echo.
echo 3. ベンチマークテスト
python tests/integration_tests/run_tests.py --benchmark
echo.
echo 全テスト完了
pause
goto menu

:quick_tests
echo.
echo クイックテスト実行中...
echo -----------------------------------
python tests/integration_tests/run_tests.py --quick
echo.
echo クイックテスト完了
pause
goto menu

:end
echo.
echo テストフレームワークを終了します
exit /b 0 