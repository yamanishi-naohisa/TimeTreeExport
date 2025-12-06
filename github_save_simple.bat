@echo off
chcp 65001 > nul
echo GitHubへの保存を開始します...
echo.

git add .
git commit -m "自動保存: %date% %time%"
git push

echo.
echo 完了しました
pause

