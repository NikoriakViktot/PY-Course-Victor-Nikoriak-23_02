
)

echo.
echo ============================================
echo   Python Course -- Select Lesson
echo ============================================
echo.

setlocal enabledelayedexpansion

:: Scan all *_student.ipynb, extract lesson number from folder prefix (04_... -> 4)
for /r %%f in (*_student.ipynb) do (
    for %%d in ("%%~dpf.") do set "_folder=%%~nxd"
    for /f "tokens=1 delims=_" %%a in ("!_folder!") do (
        set /a _num=%%a
        if !_num! GTR 0 (
            set "nb!_num!=%%f"
            set "lbl!_num!=!_folder! / %%~nf"
        )
    )
)

:: Print menu in order
set _found=0
for /l %%i in (1,1,99) do (
    if defined nb%%i (
        echo   [%%i] !lbl%%i!
        set _found=1
    )
)

if %_found%==0 (
    echo No lesson notebooks found.
    pause
    endlocal
    exit /b 1
)

echo.
set /p choice="Enter lesson number: "

if not defined nb%choice% (
    echo.
    echo [ERROR] Lesson %choice% not found.
    pause
    endlocal
    exit /b 1
)

set PORT=8891
echo.
echo Launching lesson %choice% at http://localhost:%PORT%/ ...
echo.
start /b powershell -Command "Start-Sleep 3; Start-Process 'http://localhost:%PORT%/'"
.venv\Scripts\voila.exe "!nb%choice%!" --port=%PORT%
endlocal
