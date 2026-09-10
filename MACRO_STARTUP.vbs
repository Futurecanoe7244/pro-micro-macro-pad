Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Dynamically extracts the exact, true folder path where this VBS file lives
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Executes your python script completely hidden using the verified true directory path
WshShell.Run "pythonw.exe """ & scriptPath & "\macro-app.py""", 0, False
