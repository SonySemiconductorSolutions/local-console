# OSS

We consider two levels of OSS SBOM: Packager and Application.

## Packager SBOM

Includes:

* Tools used to generate released artifacts. For example, on Windows, this might involve tools like Inno Setup.
* Software embedded into the installer.

**NOTE**: Software downloaded via a script during installation is not included in this section.

## Application SBOM

Includes all dependencies anticipated to be accessible from the application. These can be downloaded by the installer or previously installed by the user.

For example, this covers:

* Python dependencies obtained from `requirements.txt`.
* System dependencies, such as mosquitto, flatc, etc.
