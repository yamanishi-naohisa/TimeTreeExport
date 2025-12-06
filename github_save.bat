@echo off
chcp 65001 > nul
echo ========================================
echo GitHubへの保存を開始します
echo ========================================
echo.

REM 現在の変更を確認
git status
echo.
echo 上記の変更をコミットしてプッシュしますか？
pause

REM すべての変更をステージング
echo.
echo 変更をステージング中...
git add .
if %ERRORLEVEL% NEQ 0 (
    echo エラー: git add に失敗しました
    pause
    exit /b 1
)

REM コミットメッセージを生成（日時を含む）
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set date_str=%datetime:~0,4%年%datetime:~4,2%月%datetime:~6,2%日_%datetime:~8,2%時%datetime:~10,2%分
set commit_msg=自動保存: %date_str%

REM コミット
echo.
echo コミット中: %commit_msg%
git commit -m "%commit_msg%"
if %ERRORLEVEL% NEQ 0 (
    echo エラー: git commit に失敗しました
    echo 変更がないか、既にコミット済みの可能性があります
    pause
    exit /b 1
)

REM プッシュ
echo.
echo GitHubにプッシュ中...
git push
if %ERRORLEVEL% NEQ 0 (
    echo エラー: git push に失敗しました
    pause
    exit /b 1
)

echo.
echo ========================================
echo GitHubへの保存が完了しました
echo ========================================
pause

