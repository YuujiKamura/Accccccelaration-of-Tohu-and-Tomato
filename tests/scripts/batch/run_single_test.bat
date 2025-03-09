@echo off
REM 特定のテストケースのみを実行するバッチファイル
REM 使用方法: run_single_test.bat テストファイル [テストクラス.テストメソッド]

if "%~1"=="" (
    echo 使用方法: run_single_test.bat テストファイル [テストクラス.テストメソッド]
    echo 例: run_single_test.bat test_basic_new TestBasic.test_constants
    exit /b 1
)

set TEST_FILE=%~1
set TEST_METHOD=

if not "%~2"=="" (
    set TEST_METHOD=%~2
)

echo 特定のテストを実行します...
echo テストファイル: %TEST_FILE%

if "%TEST_METHOD%"=="" (
    echo.
    echo テストファイル全体を実行します
    python -m unittest %TEST_FILE%
) else (
    echo テストメソッド: %TEST_METHOD%
    echo.
    python -m unittest %TEST_FILE%.%TEST_METHOD%
)

set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo テストは正常に完了しました！
    echo.
) else (
    echo.
    echo テスト実行中にエラーが発生しました。エラーメッセージを確認してください。
    echo.
)

exit /b %EXIT_CODE% 
REM 特定のテストケースのみを実行するバッチファイル
REM 使用方法: run_single_test.bat テストファイル [テストクラス.テストメソッド]

if "%~1"=="" (
    echo 使用方法: run_single_test.bat テストファイル [テストクラス.テストメソッド]
    echo 例: run_single_test.bat test_basic_new TestBasic.test_constants
    exit /b 1
)

set TEST_FILE=%~1
set TEST_METHOD=

if not "%~2"=="" (
    set TEST_METHOD=%~2
)

echo 特定のテストを実行します...
echo テストファイル: %TEST_FILE%

if "%TEST_METHOD%"=="" (
    echo.
    echo テストファイル全体を実行します
    python -m unittest %TEST_FILE%
) else (
    echo テストメソッド: %TEST_METHOD%
    echo.
    python -m unittest %TEST_FILE%.%TEST_METHOD%
)

set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo テストは正常に完了しました！
    echo.
) else (
    echo.
    echo テスト実行中にエラーが発生しました。エラーメッセージを確認してください。
    echo.
)

exit /b %EXIT_CODE% 