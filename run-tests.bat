@echo off
REM 言知语言测试运行脚本
REM
REM 用法:
REM   run-tests.bat                - 运行全部测试
REM   run-tests.bat unit           - 仅运行单元测试
REM   run-tests.bat full           - 运行全部 + 端到端测试
REM   run-tests.bat lint           - 运行代码风格检查
REM   run-tests.bat <文件路径>     - 运行指定测试文件
REM   run-tests.bat clean          - 仅清理缓存

setlocal enabledelayedexpansion

REM 设置项目根目录
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

REM 清理字节码缓存
if "%1"=="clean" goto :CLEAN

echo ========================================
echo  言知语言测试套件
echo ========================================
echo.

:CLEAN
echo [清理字节码缓存...]
for /d /r src %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d" 2>nul
for /d /r tests %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d" 2>nul
if "%1"=="clean" (
    echo [完成] 缓存已清理
    exit /b 0
)

REM 根据参数运行不同测试
if /i "%1"=="unit" (
    echo [运行: 单元测试]
    echo.
    python -m pytest tests/unit/ -v --tb=short --strict-markers
    goto :CHECK_RESULT
)

if /i "%1"=="full" (
    echo [运行: 全部测试 + 端到端]
    echo.
    python -m pytest tests/ -v --tb=short --strict-markers
    goto :CHECK_RESULT
)

if /i "%1"=="lint" (
    echo [运行: 代码风格检查]
    echo.
    echo --- 严重错误 ---
    python -m flake8 src/yanzhi/ --count --select=E9,F63,F7,F82 --show-source --statistics
    echo.
    echo --- 风格建议 ---
    python -m flake8 src/yanzhi/ --count --exit-zero --max-complexity=15 --max-line-length=127 --statistics
    goto :CHECK_RESULT
)

if /i "%1"=="fast" (
    echo [运行: 快速测试（跳过示例）]
    echo.
    python -m pytest tests/unit/compiler/test_pre_tokenizer.py tests/unit/runtime/test_vm.py -v --tb=short
    goto :CHECK_RESULT
)

REM 默认：运行所有测试
if "%~1"=="" (
    echo [运行: 全部测试]
    echo.
    python -m pytest tests/ -v --tb=short --strict-markers
) else (
    echo [运行: %*]
    echo.
    python -m pytest %* -v --tb=short
)

:CHECK_RESULT
if errorlevel 1 (
    echo.
    echo ========================================
    echo  [失败] 有测试未通过
    echo ========================================
    exit /b 1
) else (
    echo.
    echo ========================================
    echo  [通过] 全部测试通过
    echo ========================================
    exit /b 0
)
