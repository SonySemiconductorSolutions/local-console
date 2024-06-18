function Check-Privilege
{
    # Get the ID and security principal of the current user account
    $myWindowsID = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $myWindowsPrincipal = new-object System.Security.Principal.WindowsPrincipal($myWindowsID)
    # Get the security principal for the Administrator role
    $adminRole = [System.Security.Principal.WindowsBuiltInRole]::Administrator

    $myWindowsPrincipal.IsInRole($adminRole)
}

function Display-Privilege
{
    # If we are running "as Administrator" - so change the title and background color to indicate this
    if ($(Check-Privilege)) {
        $Host.UI.RawUI.WindowTitle = $Script:MyInvocation.MyCommand.Name + " (Elevated)"
        $Host.UI.RawUI.BackgroundColor = "DarkBlue"
    }
}

function Run-Privileged([string]$PrivilegedExecPath, [string]$ExtraArgs = "")
{
    if (-not $(Check-Privilege)) {
        # We are not running "as Administrator" - so relaunch as administrator

        # First ensure we can run a script...
        $Actions = (,"Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
        if (-not [string]::IsNullOrWhiteSpace($PrivilegedExecPath)) {
            # ..then actually run this script as Administrator
            $Actions += (,"`"$PrivilegedExecPath`" $ExtraArgs")
        }

        $joint = $Actions -join "; "
        Write-LogMessage "Running '$joint' as Administrator (This will request Administrator Role)"
        $Opts = @{
            FilePath = "powershell"
            Verb = "RunAs"
            ArgumentList = $joint
        }
        Start-Process @Opts -Wait
        Write-LogMessage "Finished '$joint'"
    }
}

function Run-Unprivileged([string]$UnprivilegedExecPath, [string]$ExtraArgs = "")
{
    Start-Process -FilePath "powershell" -NoNewWindow -Wait -ArgumentList "`"$UnprivilegedExecPath`" $ExtraArgs"
}

function Set-TemporalExecutionPolicy
{
    Write-LogMessage "Temporarily setting execution policy (This will request Administrator Role)"
    Start-Process -FilePath "powershell" -Verb RunAs -Wait -ArgumentList "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    Write-LogMessage "Done"
}

function Restore-DefaultExecutionPolicy
{
    Write-LogMessage "Restoring default execution policy (This will request Administrator Role)"
    Start-Process -FilePath "powershell" -Verb RunAs -Wait -ArgumentList "Set-ExecutionPolicy -ExecutionPolicy Default -Scope CurrentUser"
    Write-LogMessage "Done"
}

function Wait-UserInput([int]$wait = 5)
{
    Write-LogMessage "Will wait for $wait seconds or on keypress..."
    Start-Sleep -milliseconds 100;
    $Host.ui.RawUI.FlushInputBuffer();
    $counter = 0
    while(!$Host.UI.RawUI.KeyAvailable -and ($counter++ -lt $wait))
    {
        [Threading.Thread]::Sleep( 1000 )
    }
}

function Get-ProgramFilesPath
{
    # Get the path to the Program Files directory
    $folderSpec = [System.Environment+SpecialFolder]::ProgramFiles
    return [System.Environment]::GetFolderPath($folderSpec)
}

function Test-ExecutablePath([string]$Path)
{
    # Check if the path exists and is a file
    if (Test-Path $Path -PathType Leaf) {
        # Get the item and check if its extension is '.exe'
        $item = Get-Item $Path
        if ($item.Extension -eq '.exe') {
            return $true
        } else {
            Write-Debug "The path is not an executable file (.exe)."
            return $false
        }
    } else {
        Write-Debug "The path does not exist or is not a file."
        return $false
    }
}

function Refresh-Path
{
    $systemPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)
    $combinedPath = $systemPath + ";" + $userPath

    # Remove duplicate entries to clean up the PATH
    $uniquePath = $combinedPath -split ';' | Select-Object -Unique | Where-Object { $_ -ne '' }

    [System.Environment]::SetEnvironmentVariable("Path", ($uniquePath -join ';'), [System.EnvironmentVariableTarget]::Process)
}

function Write-LogMessage([string]$Message)
{
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"

    if (-not [string]::IsNullOrWhiteSpace($RedirectLogPath)) {
        Write-Host $logMessage *>> "$RedirectLogPath"
    } else {
        Write-Host $logMessage
    }
}

$DefaultInstallPath = Join-Path $env:LOCALAPPDATA "Programs" | Join-Path -ChildPath "LocalConsole"
