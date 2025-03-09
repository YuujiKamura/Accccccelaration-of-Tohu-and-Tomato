@echo off
REM ファイル変更を監視して自動的にテストを実行する
REM 使用方法: watch_tests.bat [オプション]

REM watchdogがインストールされているか確認
python -c "import watchdog" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo watchdogパッケージがインストールされていません。
    echo インストールしますか？ (Y/N)
    set /p INSTALL=
    if /i "%INSTALL%"=="Y" (
        echo watchdogをインストールしています...
        pip install watchdog
        if %ERRORLEVEL% NEQ 0 (
            echo インストールに失敗しました。
            echo 手動でインストールしてください: pip install watchdog
            exit /b 1
        )
    ) else (
        echo インストールをスキップします。
        echo watch_tests.pyを実行するにはwatchdogが必要です。
        exit /b 1
    )
)

REM ヘルプを表示
if "%1"=="--help" (
    echo 使用方法: watch_tests.bat [オプション]
    echo.
    echo オプション:
    echo   --dir ^<DIR^>        監視するディレクトリ
    echo   --fast             変更されたファイルに関連するテストのみ実行
    echo   --command ^<CMD^>    使用するテストコマンド
    echo   --help             このヘルプメッセージを表示
    echo.
    echo 例:
    echo   watch_tests.bat --fast
    echo   watch_tests.bat --dir src --command "python run_tests.bat"
    exit /b 0
)

REM 引数の処理
set WATCH_ARGS=
set COMMAND="python run_auto_tests.py --verbosity=1"

:parse_args
if "%1"=="" goto run
if "%1"=="--fast" (
    set WATCH_ARGS=%WATCH_ARGS% --fast
    shift
    goto parse_args
)
if "%1"=="--dir" (
    set WATCH_ARGS=%WATCH_ARGS% --dir "%2"
    shift
    shift
    goto parse_args
)
if "%1"=="--command" (
    set COMMAND=%2
    shift
    shift
    goto parse_args
)
REM 知らない引数はそのまま渡す
set WATCH_ARGS=%WATCH_ARGS% %1
shift
goto parse_args

:run
cls
echo REPループ（Read-Eval-Print）を高速化するファイル監視を開始します
echo.
echo ファイルを変更すると、自動的にテストが実行されます
echo （Ctrl+C で終了）
echo.

REM watch_tests.pyを実行
python watch_tests.py --command %COMMAND% %WATCH_ARGS%

exit /b %ERRORLEVEL% 
REM ファイル変更を監視して自動的にテストを実行する
REM 使用方法: watch_tests.bat [オプション]

REM watchdogがインストールされているか確認
python -c "import watchdog" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo watchdogパッケージがインストールされていません。
    echo インストールしますか？ (Y/N)
    set /p INSTALL=
    if /i "%INSTALL%"=="Y" (
        echo watchdogをインストールしています...
        pip install watchdog
        if %ERRORLEVEL% NEQ 0 (
            echo インストールに失敗しました。
            echo 手動でインストールしてください: pip install watchdog
            exit /b 1
        )
    ) else (
        echo インストールをスキップします。
        echo watch_tests.pyを実行するにはwatchdogが必要です。
        exit /b 1
    )
)

REM ヘルプを表示
if "%1"=="--help" (
    echo 使用方法: watch_tests.bat [オプション]
    echo.
    echo オプション:
    echo   --dir ^<DIR^>        監視するディレクトリ
    echo   --fast             変更されたファイルに関連するテストのみ実行
    echo   --command ^<CMD^>    使用するテストコマンド
    echo   --help             このヘルプメッセージを表示
    echo.
    echo 例:
    echo   watch_tests.bat --fast
    echo   watch_tests.bat --dir src --command "python run_tests.bat"
    exit /b 0
)

REM 引数の処理
set WATCH_ARGS=
set COMMAND="python run_auto_tests.py --verbosity=1"

:parse_args
if "%1"=="" goto run
if "%1"=="--fast" (
    set WATCH_ARGS=%WATCH_ARGS% --fast
    shift
    goto parse_args
)
if "%1"=="--dir" (
    set WATCH_ARGS=%WATCH_ARGS% --dir "%2"
    shift
    shift
    goto parse_args
)
if "%1"=="--command" (
    set COMMAND=%2
    shift
    shift
    goto parse_args
)
REM 知らない引数はそのまま渡す
set WATCH_ARGS=%WATCH_ARGS% %1
shift
goto parse_args

:run
cls
echo REPループ（Read-Eval-Print）を高速化するファイル監視を開始します
echo.
echo ファイルを変更すると、自動的にテストが実行されます
echo （Ctrl+C で終了）
echo.

REM watch_tests.pyを実行
python watch_tests.py --command %COMMAND% %WATCH_ARGS%

exit /b %ERRORLEVEL% 