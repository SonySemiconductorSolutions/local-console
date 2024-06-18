$rootPath = Split-Path $MyInvocation.MyCommand.Path -parent
$utils = Join-Path -Path $rootPath -ChildPath "utils.ps1"
. $utils

function Main
{
    Set-TemporalExecutionPolicy

    Write-LogMessage "Uninstalling Local Console"

    # Construct the full path to the new directory within APPDATA
    $fullPath = $DefaultInstallPath
    if (Test-Path -Path $fullPath)
    {
        Write-LogMessage "Removing program files"
        Remove-Item -Path $fullPath -Recurse -Force
    }

    $WshShell = New-Object -comObject WScript.Shell
    $IconPath = Join-Path -Path $WshShell.SpecialFolders("Desktop") -ChildPath "Local Console.lnk"
    if (Test-Path -Path $IconPath)
    {
        Write-LogMessage "Removing desktop shortcut"
        Remove-Item -Path $IconPath -Force
    }

    Write-LogMessage "Removing configuration directory"
    $ConfigPath = Join-Path $env:APPDATA -ChildPath "local-console"
    Remove-Item -Path $ConfigPath -Recurse -Force

    Restore-DefaultExecutionPolicy
    Wait-UserInput
}

Main
