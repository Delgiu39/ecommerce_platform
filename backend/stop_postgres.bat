@echo off
echo Arresto del server PostgreSQL portatile...
"%~dp0postgresql\pgsql\bin\pg_ctl.exe" -D "%~dp0postgresql\data" stop
echo PostgreSQL arrestato.
pause
