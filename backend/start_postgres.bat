@echo off
set PGPASSWORD=postgres
echo Avvio del server PostgreSQL portatile...
"%~dp0postgresql\pgsql\bin\pg_ctl.exe" -D "%~dp0postgresql\data" -l "%~dp0postgresql\pg.log" start
echo PostgreSQL avviato.
pause
