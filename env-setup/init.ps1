if (-not (Get-Module -ListAvailable -Name WSLTools)) {
    Install-Module -Name WSLTools -Force
} 

Import-Module WSLTools -WarningAction SilentlyContinue
if (-not (Ensure-WSL)) {
	$question = "Yes","No"
	$selected = Get-Select -Prompt "[OPER] Would you like to install HyperV and WSL now?" -Options $question
	if ($selected -eq "Yes") {
		iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/rgryta/PowerShell-WSLTools/main/install-wsl.ps1'))
		Write-Host "Reboot your system now and then restart the script"
	}
	if ($selected -eq "No") {
		Write-Host "Please set up HyperV and WSL manually and then relaunch the script"
	}
	return $false
}

$scriptPath = split-path -parent $MyInvocation.MyCommand.Definition
$distro = 'ubuntu-noprint'
$ignr = wsl --unregister $distro

WSL-Ubuntu-Install -DistroAlias $distro -InstallPath $scriptPath

wsl -d $distro -u root -e sh -c "apt-get install -y apt-utils sudo git python3 python3-pip python3-venv"

wsl -d $distro -e sh -c "cd ``wslpath -a '$scriptPath'``/.. && ./init.sh"
	
# python3 -m pip install --upgrade build
# python3 -m build