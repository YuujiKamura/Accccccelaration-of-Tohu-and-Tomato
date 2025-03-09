@echo off
REM ゲームの自動テストを実行するためのバッチファイル
REM 使用方法: run_tests.bat [テストパターン]

echo 自動テスト実行を開始します...

REM テストパターンが指定されているかチェック
if "%~1"=="" (
    echo すべてのテストを実行します
    python run_auto_tests.py --verbosity=2 --report
) else (
    echo パターン %1 に一致するテストを実行します
    python run_auto_tests.py --pattern=%1 --verbosity=2 --report
)

REM 実行結果のステータスコードを取得
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo テストは正常に完了しました！
    echo.
) else (
    echo.
    echo テスト実行中にエラーが発生しました。詳細はレポートを確認してください。
    echo.
)

exit /b %EXIT_CODE% 
REM ゲームの自動テストを実行するためのバッチファイル
REM 使用方法: run_tests.bat [テストパターン]

echo 自動テスト実行を開始します...

REM テストパターンが指定されているかチェック
if "%~1"=="" (
    echo すべてのテストを実行します
    python run_auto_tests.py --verbosity=2 --report
) else (
    echo パターン %1 に一致するテストを実行します
    python run_auto_tests.py --pattern=%1 --verbosity=2 --report
)

REM 実行結果のステータスコードを取得
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo テストは正常に完了しました！
    echo.
) else (
    echo.
    echo テスト実行中にエラーが発生しました。詳細はレポートを確認してください。
    echo.
)

exit /b %EXIT_CODE% 