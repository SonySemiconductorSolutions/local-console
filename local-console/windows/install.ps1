Param (
	[String] $AppInstallPath,
    [String] $WheelPath
)
$UseWheel = -not [string]::IsNullOrWhiteSpace($WheelPath)

$RedirectLogPath = [System.Environment]::GetEnvironmentVariable("LOG_PS1", [System.EnvironmentVariableTarget]::Process)
$DoRedirect = -not [string]::IsNullOrWhiteSpace($RedirectLogPath)

$rootPath = Split-Path $MyInvocation.MyCommand.Path -parent
$utils = Join-Path $rootPath "utils.ps1"
. $utils

function Main
{
    if ($(Check-Privilege)) {
        Write-Error "This script must NOT be run as an Administrator role"
        Wait-UserInput 10
        Exit 1
    }

    $stepsPath = Join-Path $rootPath "steps"
    $scriptSys = Join-Path $stepsPath "sys.ps1"
    $scriptApp = Join-Path $stepsPath "app.ps1"

    Write-LogMessage "Installing system dependencies"
    $SysRedirectArgs = ""
    $SysLogFile = "$RedirectLogPath-sys"
    if ($DoRedirect) {
        $SysRedirectArgs = "-TranscriptPath `"$SysLogFile`""
    }
    try {
        Run-Privileged "$scriptSys" "$SysRedirectArgs"
        if ($DoRedirect) {
            cat "$SysLogFile" >> $RedirectLogPath
            rm "$SysLogFile"
        }
    }
    catch {
        Write-LogMessage "Could not install system dependencies"
        return 1
    }

    Write-LogMessage "Done installing system dependencies"

    if ([string]::IsNullOrWhiteSpace($AppInstallPath)) {
        $AppInstallPath = $DefaultInstallPath
    }

    Write-LogMessage "Installing Local Console"
    $AppInstallArgs = "-InstallPath `"$AppInstallPath`""
    $AppRedirectArgs = ""
    $AppLogFile = "$RedirectLogPath-app"
    if ($UseWheel) {
        $AppRedirectArgs += " -WheelPath `"$WheelPath`""
    }
    if ($DoRedirect) {
        $AppRedirectArgs += " -TranscriptPath `"$AppLogFile`""
    }
    Run-Unprivileged "$scriptApp" "$AppInstallArgs $AppRedirectArgs"
    if ($DoRedirect) {
        cat "$AppLogFile" >> $RedirectLogPath
        rm "$AppLogFile"
    }
    Write-LogMessage "Done installing Local Console"

    Restore-DefaultExecutionPolicy
    Wait-UserInput
}

Main
