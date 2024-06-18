Param (
	[String] $InstallPath,
	[String] $WheelPath,
    [String] $TranscriptPath
)
$DoRedirect = -not [string]::IsNullOrWhiteSpace($TranscriptPath)

$rootPath = Split-Path -parent $MyInvocation.MyCommand.Path | Split-Path -parent
$utils = Join-Path $rootPath "utils.ps1"
. $utils

# URLs of binary dependencies
$DepURLFlatc = 'https://github.com/google/flatbuffers/releases/download/v24.3.25/Windows.flatc.binary.zip'

function Main
{
    if ($DoRedirect) {
        Start-Transcript -Path "$TranscriptPath" -Append
    }

    Refresh-Path
    Create-AppDataDirectory -Path $InstallPath
    $virtualenvDir = Join-Path $InstallPath "virtualenv"
    Create-PythonEnvWithExecutable -VirtualenvDir $virtualenvDir -WheelPath $WheelPath

    $binPath = Join-Path $VirtualenvDir "Scripts"
    Get-FlatcBinary -ScriptsDir $binPath
    Create-DesktopShortcut -VirtualenvDir $virtualenvDir
}

function Create-PythonEnvWithExecutable([string]$VirtualenvDir, [string]$WheelPath)
{
    # Check if the directory already exists
    if (Test-Path -Path $VirtualenvDir -PathType Container) {
        Write-LogMessage "Virtualenv parent folder already exists at $VirtualenvDir"
    } else {
        # Attempt to create the directory
        try {
            New-Item -Path $VirtualenvDir -ItemType Directory | Out-Null
            Write-LogMessage "Virtualenv parent created successfully: $VirtualenvDir"
        } catch {
            Write-LogMessage "Failed to create parent: $_"
        }
    }

    $PythonAtVenv = Join-Path $VirtualenvDir "Scripts" `
                  | Join-Path -ChildPath "python.exe"
    if (Test-Path $PythonAtVenv -PathType Leaf) {
        Write-LogMessage "Virtual environment is already present."
    } else {
        Write-LogMessage "Virtual environment will be created in $VirtualenvDir"
        python -m venv $VirtualenvDir
        Write-LogMessage "Virtual environment created."
    }

    $UseWheel = -not [string]::IsNullOrWhiteSpace($WheelPath)
    if ($UseWheel) {
        & $PythonAtVenv -m pip install "$WheelPath"
    }
    else {
        # Install from the repo sources
        $repoPath = Split-Path -parent $Script:MyInvocation.MyCommand.Path `
                  | Split-Path -parent `
                  | Split-Path -parent
        & $PythonAtVenv -m pip install "$repoPath"
    }

    if ($LASTEXITCODE -eq 0) {
        Write-LogMessage "Local Console has been installed."
    } else {
        Write-Error "Error activating the virtualenv"
        Exit 1
    }

    Write-LogMessage "Virtual environment has been updated."
}

function Get-FlatcBinary([string]$ScriptsDir)
{
    $flatcPath = Join-Path $ScriptsDir "flatc.exe"

    if (Test-Path $flatcPath -PathType Leaf) {
        Write-LogMessage "Flatc already installed at $ScriptsDir"
        return
    }

    # Download the zip file
    $zipPath = Join-Path $env:TEMP "tempExecutable.zip"

    # Initialize a flag to indicate the download success status
    $downloadSuccessful = $false
    # Loop until the download is successful
    while (-not $downloadSuccessful) {
        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $DepURLFlatc -OutFile $zipPath -Verbose:$false
            $downloadSuccessful = $true
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            Write-Output "Download failed (got code $statusCode). Retrying..."
            Start-Sleep -Seconds 5
        }
    }
    Write-LogMessage "Flatc Zipball downloaded."


    # Initialize a flag to indicate the download success status
    $unpackSuccesful = $false
    # Loop until the download is successful
    while (-not $unpackSuccesful) {
        try {
            $ProgressPreference = 'SilentlyContinue'
            # Unpack the zip file directly into the virtual environment's Scripts/ directory
            Expand-Archive -Path $zipPath -DestinationPath $ScriptsDir -Force -Verbose:$false
            Write-LogMessage "Flatc Executable unpacked into $ScriptsDir"
            $unpackSuccesful = $true
        } catch {
            Write-Output "Unpack failed (got $($_.Exception)). Retrying..."
            Start-Sleep -Seconds 2
        }
    }

    # Cleanup the downloaded zip file
    Remove-Item -Path $zipPath
}

function Create-AppDataDirectory([string]$Path)
{
    # Check if the directory already exists
    if (Test-Path -Path $Path) {
        Write-LogMessage "Directory already exists: $Path"
    } else {
        # Attempt to create the directory
        try {
            New-Item -Path $Path -ItemType Directory | Out-Null
            Write-LogMessage "Directory created successfully: $Path"
        } catch {
            Write-LogMessage "Failed to create directory: $_"
        }
    }
}

function Create-DesktopShortcut([string]$VirtualenvDir)
{
    $WshShell = New-Object -comObject WScript.Shell
    $DestinationPath = Join-Path $WshShell.SpecialFolders("Desktop") "Local Console.lnk"

    # If icon already exists, just remove it so that we make sure it is
    # kept up to date since recreating has zero cost.
    if (Test-Path $DestinationPath -PathType Leaf) {
        Remove-Item -Path $DestinationPath
    }

    $SourceExe = Join-Path $VirtualenvDir "Scripts" `
               | Join-Path -ChildPath "local-console.exe"
    $Command = 'gui'

    $Shortcut = $WshShell.CreateShortcut($DestinationPath)
    $Shortcut.TargetPath = $SourceExe
    $Shortcut.Arguments = $Command
    $Shortcut.WorkingDirectory = $HOME
    $Shortcut.Description = "Starts the Local Console"
    #$Shortcut.IconLocation = ""
    $Shortcut.Save()

    Write-LogMessage "Created desktop shortcut at: $DestinationPath"
}

Main
