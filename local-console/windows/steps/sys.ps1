# Copyright 2024 Sony Semiconductor Solutions Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This file incorporates material from https://github.com/dcos/dcos/tree/2.1.0-beta1, which is licensed
# under the Apache License, Version 2.0
#
# - This file re-uses some components from,
#   https://github.com/dcos/dcos/blob/2.1.0-beta1/gen/build_deploy/powershell/dcos_install.ps1
#
# SPDX-License-Identifier: Apache-2.0
Param (
	[String] $TranscriptPath
)
$DoRedirect = -not [string]::IsNullOrWhiteSpace($TranscriptPath)

$rootPath = Split-Path -parent $MyInvocation.MyCommand.Path | Split-Path -parent
$utils = Join-Path $rootPath "utils.ps1"
. $utils

$vcredistDir = Split-Path -parent $MyInvocation.MyCommand.Path | Join-Path -ChildPath "vcredist"
. (Join-Path $vcredistDir "Get-InstalledSoftware.ps1")
. (Join-Path $vcredistDir "Get-InstalledVcRedist.ps1")

# Current limitations:
# - This script assumes a 64-bit windows installation

# URLs of binary dependencies
$DepURLMosquitto = 'https://mosquitto.org/files/binary/win64/mosquitto-2.0.9-install-windows-x64.exe'
$DepURLPython = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
$DepURLGit = 'https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe'
$DepURLVcredist = 'https://aka.ms/vs/17/release/vc_redist.x64.exe'

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

    Get-CompatibleVCRedist
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
            $persistedPaths = $persistedPaths + $Path | Where-Object { $_ }
            [Environment]::SetEnvironmentVariable('Path', $persistedPaths -join ';', $containerType)
        }
    }

    $envPaths = $env:Path -split ';'
    if ($envPaths -notcontains $Path) {
        $envPaths = $envPaths + $Path | Where-Object { $_ }
        $env:Path = $envPaths -join ';'
    }
}

function Initialize-Mosquitto
{
    # Check if the Mosquitto service has been added and remove it if found
    $service = Get-Service -DisplayName "*mosquitto*" -ErrorAction SilentlyContinue

    # Check if the service was found
    if ($null -ne $service) {
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

function Get-CompatibleVCRedist
{
    # Check if the Visual C++ Redistributable for Visual Studio 2012+ is installed
    if (Find-RequiredVCredist) {
        Write-LogMessage "Visual C++ Redistributable for Visual Studio 2012+ is already installed"
        return
    }

    # Download the installer
    Write-LogMessage "Downloading Visual C++ Redistributable for Visual Studio 2022..."

    # Temporary target
    $downloadPath = Join-Path $env:TEMP "vcredist.exe"
    Invoke-WebRequest -Uri $DepURLVcredist -OutFile $downloadPath

    Write-LogMessage "Installing Visual C++ Redistributable for Visual Studio 2022"
    try {
        # Create parameters with -ArgumentList set based on Install/SilentInstall properties in the manifest
        $params = @{
            FilePath     = $downloadPath
            ArgumentList = "/install /passive /norestart"
            PassThru     = $true
            Wait         = $true
            NoNewWindow  = $true
            Verbose      = $VerbosePreference
            ErrorAction  = "Continue"
        }
        Start-Process @params
    }
    catch {
        throw $_
    }

    # Check for actual success. Reference:
    # https://github.com/aaronparker/vcredist/blob/42581ac57/VcRedist/VisualCRedistributables.json#L83C28-L83C68
    $ProductCode = '{5af95fd8-a22e-458f-acee-c61bd787178e}'
    $Installed = Get-InstalledVcRedist | Where-Object { $_.ProductCode -eq $ProductCode }
    if ($Installed) {
        Write-LogMessage "Finished installing Visual C++ Redistributable for Visual Studio 2022"
    }
}

function Find-RequiredVCredist
{
    $found = $false

    $installed = Get-InstalledVcRedist
    foreach ($entry in $installed) {
        if ( `
            ([System.Version]($entry.Version) -gt [System.Version]"12.0") `
            -and ($entry.Architecture -eq "x64") `
           ) {
            $found = $true
        } }

    $found
}

Main
