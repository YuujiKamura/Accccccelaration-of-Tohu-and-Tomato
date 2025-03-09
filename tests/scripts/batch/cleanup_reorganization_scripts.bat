@echo off
echo =================================================
echo 不要な整理スクリプトを削除します
echo =================================================

echo バックアップフォルダを作成中...
mkdir reorganization_scripts_backup
echo.

echo スクリプトのバックアップを作成中...
copy auto_reorganize.py reorganization_scripts_backup\
copy auto_reorganize.bat reorganization_scripts_backup\
copy smart_reorganize.py reorganization_scripts_backup\
copy smart_reorganize.bat reorganization_scripts_backup\
copy organize_project_safe.py reorganization_scripts_backup\
copy organize_project_safe.bat reorganization_scripts_backup\
copy organize_project.py reorganization_scripts_backup\ 2>nul
copy organize_project.bat reorganization_scripts_backup\ 2>nul
echo.

echo 不要なスクリプトを削除中...
del auto_reorganize.py
del auto_reorganize.bat
del smart_reorganize.py
del smart_reorganize.bat
del organize_project_safe.py
del organize_project_safe.bat
del organize_project.py 2>nul
del organize_project.bat 2>nul
echo.

echo 新しい統合スクリプトの実行権限を確認...
echo @echo off > run_project_reorganizer.bat
echo python project_reorganizer.py %* >> run_project_reorganizer.bat
echo pause >> run_project_reorganizer.bat
echo.

echo =================================================
echo 処理が完了しました。
echo 以下のファイルが利用可能です：
echo  - project_reorganizer.py （統合スクリプト）
echo  - run_project_reorganizer.bat （実行用バッチ）
echo.
echo 元のスクリプトはreorganization_scripts_backupに
echo バックアップされています。
echo =================================================

pause 