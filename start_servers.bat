@echo off
echo Starting frontend server...
start cmd /k "cd C:\voting-system\frontend && npm start"

echo Starting backend server...
start cmd /k "cd C:\voting-system\backend && python .\app.py"

echo Both servers are running.
pause
