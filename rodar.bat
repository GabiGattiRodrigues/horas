@echo off
setlocal enableextensions
chcp 65001 >nul 2>&1
title Horas
cd /d "%~dp0"
set PYTHONUTF8=1

echo.
echo  ==========================================================
echo    Horas - quanto prometer de prazo de entrega
echo  ==========================================================
echo.

rem --- 1. Onde esta o Python?
set "PY="
where py >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto python_ok
where python >nul 2>&1
if not errorlevel 1 set "PY=python"
:python_ok

if not defined PY (
  echo  [ X ]  Nao encontrei o Python nesta maquina.
  echo         Instale em https://www.python.org/downloads/
  echo         e marque "Add Python to PATH" antes de clicar em Install.
  pause
  exit /b 1
)
echo  [ 1/4 ]  Python encontrado.

rem --- 2. Ambiente isolado
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" (
  echo  [ 2/4 ]  Criando o ambiente isolado ^(so na primeira vez^)...
  %PY% -m venv .venv
  if not exist "%VPY%" (
    echo  [ X ]  Nao consegui criar o ambiente .venv
    pause
    exit /b 1
  )
) else (
  echo  [ 2/4 ]  Ambiente isolado ja existe.
)

rem --- 3. Bibliotecas (so reinstala se algum requirements mudar)
set "MARCA=.venv\instalado.txt"
for %%F in (requirements.txt) do set "REQ1=%%~tF %%~zF"
for %%F in (requirements-notebook.txt) do set "REQ2=%%~tF %%~zF"
set "REQ=%REQ1% %REQ2%"
set "JAINSTALADO="
if exist "%MARCA%" set /p JAINSTALADO=<"%MARCA%"
if "%JAINSTALADO%"=="%REQ%" goto deps_prontas
echo  [ 3/4 ]  Instalando as bibliotecas. Leva alguns minutos na primeira vez.
echo.
"%VPY%" -m pip install --upgrade pip --disable-pip-version-check --retries 5 --timeout 60
"%VPY%" -m pip install -r requirements.txt -r requirements-notebook.txt --disable-pip-version-check --retries 5 --timeout 60
if errorlevel 1 (
  echo.
  echo  [ X ]  A instalacao falhou - quase sempre e conexao. Rode de novo.
  pause
  exit /b 1
)
>"%MARCA%" echo %REQ%
goto artefatos

:deps_prontas
echo  [ 3/4 ]  Bibliotecas ja instaladas.

rem --- 4. Resultados do modelo (o app le a pasta artifacts, nao precisa da base)
:artefatos
if exist "artifacts\modelo_ago2018.txt" (
  echo  [ 4/4 ]  Resultados do modelo ja existem em artifacts.
  goto abrir
)
echo  [ 4/4 ]  Resultados nao encontrados. Gerando a partir da base da Olist...
if not exist "data" mkdir data
if not exist "data\olist_orders_dataset.csv" (
  echo         Baixando a base do GitHub da Olist, pode levar uns minutos...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/olist/work-at-olist-data/archive/refs/heads/master.zip' -OutFile 'data\olist.zip'"
  powershell -NoProfile -Command "Expand-Archive -Path 'data\olist.zip' -DestinationPath 'data\_tmp' -Force"
  copy /y "data\_tmp\work-at-olist-data-master\datasets\*.csv" "data\" >nul
  rmdir /s /q "data\_tmp"
  del /q "data\olist.zip"
)
if not exist "data\olist_orders_dataset.csv" (
  echo  [ X ]  Nao consegui baixar a base da Olist.
  echo         Coloque os CSVs dentro da pasta data e rode de novo.
  pause
  exit /b 1
)
"%VPY%" scripts\gerar_artefatos.py
if errorlevel 1 (
  echo.
  echo  [ X ]  Nao consegui gerar os resultados. A mensagem esta acima.
  pause
  exit /b 1
)

:abrir
rem --- Evita o Streamlit parar pedindo e-mail na primeira execucao
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit" >nul 2>&1
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  >"%USERPROFILE%\.streamlit\credentials.toml" echo [general]
  >>"%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)
echo.
echo  Abrindo no navegador. Se nao abrir sozinho, entre em http://localhost:8501
echo  Para fechar: Ctrl+C aqui, ou feche esta janela.
echo.
echo  Para refazer os resultados do zero, apague a pasta artifacts e rode de novo.
echo.
"%VPY%" -m streamlit run app.py --server.headless false
if errorlevel 1 (
  echo.
  echo  [ X ]  O app encerrou com erro. A mensagem esta acima.
  pause
)
endlocal
