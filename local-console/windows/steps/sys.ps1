Param (
	[String] $TranscriptPath
)
$DoRedirect = -not [string]::IsNullOrWhiteSpace($TranscriptPath)

$rootPath = Split-Path -parent $MyInvocation.MyCommand.Path | Split-Path -parent
$utils = Join-Path $rootPath "utils.ps1"
. $utils

# Current limitations:
# - This script assumes a 64-bit windows installation

# URLs of binary dependencies
$DepURLMosquitto = 'https://mosquitto.org/files/binary/win64/mosquitto-2.0.9-install-windows-x64.exe'
$DepURLPython = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
$DepURLGit = 'https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe'

function Main
{
    if ($DoRedirect) {
        Start-Transcript -Path "$TranscriptPath" -Append
    }

    if (-not $(Check-Privilege)) {
        Write-Error "This script must be run as an Administrator role"
        Exit
    }
    Display-Privilege

    Get-Mosquitto
    Initialize-Mosquitto
    Set-MosquittoPath
    Get-Git
    Get-Python311

    Wait-UserInput 5
}

$MosquittoInstallPath = "$(Get-ProgramFilesPath)\mosquitto"

function Get-Mosquitto
{
    $MosquittoExecPath = Join-Path $MosquittoInstallPath "mosquitto.exe"
    if (Test-ExecutablePath -Path $MosquittoExecPath)
    {
        Write-LogMessage "Mosquitto is already installed."
        return
    }

    # Download the installer
    Write-LogMessage "Downloading installer for the Mosquitto MQTT broker..."

    # Temporary target
    $downloadPath = Join-Path $env:TEMP "mosquitto-installer.exe"
    Invoke-WebRequest -Uri $DepURLMosquitto -OutFile $downloadPath

    # Install silently
    Write-LogMessage "Installing the Mosquitto MQTT broker..."
    Start-Process -FilePath $downloadPath -ArgumentList '/S' -Wait

    # Cleanup downloaded installer
    Remove-Item -Path $downloadPath -Force

    Write-LogMessage "Mosquitto installation complete."
}

function Set-MosquittoPath
{
    try {
        Get-Command -Type Application -ErrorAction Stop -Name "mosquitto" > $null
        Write-LogMessage "Mosquitto is already in the system's PATH"
    } catch [System.Management.Automation.CommandNotFoundException] {
        Write-LogMessage "Adding Mosquitto to the system's PATH"
        Add-EnvPath $MosquittoInstallPath "Machine"
    }
}

function Add-EnvPath {
    param(
        [Parameter(Mandatory=$true)]
        [string] $Path,

        [ValidateSet('Machine', 'User', 'Session')]
        [string] $Container = 'Session'
    )

    if ($Container -ne 'Session') {
        $containerMapping = @{
            Machine = [EnvironmentVariableTarget]::Machine
            User = [EnvironmentVariableTarget]::User
        }
        $containerType = $containerMapping[$Container]

        $persistedPaths = [Environment]::GetEnvironmentVariable('Path', $containerType) -split ';'
        if ($persistedPaths -notcontains $Path) {
            $persistedPaths = $persistedPaths + $Path | where { $_ }
            [Environment]::SetEnvironmentVariable('Path', $persistedPaths -join ';', $containerType)
        }
    }

    $envPaths = $env:Path -split ';'
    if ($envPaths -notcontains $Path) {
        $envPaths = $envPaths + $Path | where { $_ }
        $env:Path = $envPaths -join ';'
    }
}

function Initialize-Mosquitto
{
    # Check if the Mosquitto service has been added and remove it if found
    $service = Get-Service -DisplayName "*mosquitto*" -ErrorAction SilentlyContinue

    # Check if the service was found
    if ($service -ne $null) {
        Write-LogMessage "Found Windows Service for Mosquitto. Preparing to remove..."
        Write-LogMessage "DisplayName: $($service.DisplayName)"
        Write-LogMessage "Status: $($service.Status)"
        Write-LogMessage "ServiceName: $($service.Name)"
        Write-LogMessage "StartType: $($service.StartType)"

        # Stop the service if it's running
        if ($service.Status -eq 'Running') {
            Write-LogMessage "Stopping the Mosquitto service..."
            Stop-Service -Name $service.Name -Force
            # Ensure the service has stopped
            $service.WaitForStatus('Stopped', '00:00:30')
        }

        # Remove the service
        Write-LogMessage "Removing the Mosquitto service..."
        $deleteCmd = "sc.exe delete $($service.Name)"
        Invoke-Expression $deleteCmd

        Write-LogMessage "Mosquitto service removed successfully."
    } else {
        Write-LogMessage "Windows Service for Mosquitto is not installed or does not exist. Continuing."
    }
}

function Get-Python311
{
    # Check if Python 3.11 is installed
    try {
        $PythonVersion = python --version 2>&1
        if ($PythonVersion -like "*Python 3.11*") {
            Write-LogMessage "Python 3.11 is already installed."
            return
        } else {
            Write-LogMessage "Python 3.11 is not installed. Current version: $PythonVersion"
        }
    } catch {
        Write-LogMessage "Python is not installed."
    }

    # Temporary target
    $installerPath = Join-Path $env:TEMP "python-3.11-installer.exe"

    # Download the installer
    Write-LogMessage "Downloading installer for Python 3.11..."
    Invoke-WebRequest -Uri $DepURLPython -OutFile $installerPath

    # Install Python 3.11
    Write-LogMessage "Installing Python 3.11..."
    Start-Process -FilePath $installerPath -Args "/quiet InstallAllUsers=1 PrependPath=1" -Wait -NoNewWindow

    # Cleanup the installer
    Remove-Item -Path $installerPath -Force

    Write-LogMessage "Python 3.11 installation complete."
}

function Get-Git
{

    $GitExecPath = "$(Get-ProgramFilesPath)\Git\bin\git.exe"
    if (Test-ExecutablePath -Path $GitExecPath)
    {
        Write-LogMessage "Git is already installed."
        return
    }

    # Download the installer
    Write-LogMessage "Downloading Git installer..."

    # Temporary target
    $downloadPath = Join-Path $env:TEMP "Git-Installer.exe"
    Invoke-WebRequest -Uri $DepURLGit -OutFile $downloadPath

    # Install silently
    Write-LogMessage "Installing Git..."
    Start-Process -FilePath $downloadPath -Args '/SILENT' -Wait -NoNewWindow

    # Cleanup
    Remove-Item -Path $downloadPath -Force

    Write-LogMessage "Git installation complete."
}

Main
