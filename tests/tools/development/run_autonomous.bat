@echo off
REM 自律テストエンジンを実行するバッチファイル
REM 使用方法: run_autonomous.bat [オプション]

echo 自律的なテスト実行エンジンを起動します...
echo この「暴走列車」は、自動的にテストを実行し、問題を修正し続けます。
echo ユーザーの介入なしに、テストが全て成功するまで走り続けます。
echo.
echo 警告: このスクリプトはコードを自動的に修正します。
echo バックアップを作成する場合は --backup オプションを使用してください。
echo.
echo (進行中にCtrl+Cで中断できます)
echo.

REM 引数をそのまま渡す
python autonomous_test_engine.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 自律テストエンジンは正常に終了しました。
    echo すべてのテストが成功しています！
) else (
    echo.
    echo 自律テストエンジンは問題を検出して終了しました。
    echo 詳細は上記のログを確認してください。
)

exit /b %ERRORLEVEL% 
REM 自律テストエンジンを実行するバッチファイル
REM 使用方法: run_autonomous.bat [オプション]

echo 自律的なテスト実行エンジンを起動します...
echo この「暴走列車」は、自動的にテストを実行し、問題を修正し続けます。
echo ユーザーの介入なしに、テストが全て成功するまで走り続けます。
echo.
echo 警告: このスクリプトはコードを自動的に修正します。
echo バックアップを作成する場合は --backup オプションを使用してください。
echo.
echo (進行中にCtrl+Cで中断できます)
echo.

REM 引数をそのまま渡す
python autonomous_test_engine.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 自律テストエンジンは正常に終了しました。
    echo すべてのテストが成功しています！
) else (
    echo.
    echo 自律テストエンジンは問題を検出して終了しました。
    echo 詳細は上記のログを確認してください。
)

exit /b %ERRORLEVEL% 