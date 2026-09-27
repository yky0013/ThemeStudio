$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$principal=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Windows administrator authorization is required for this bounded test.'}
Add-Type -AssemblyName System.Drawing
$qaRoot=Join-Path $projectRoot 'qa\runtime\admin-native'
$release=Join-Path $projectRoot 'release\ThemeStudio'
$dataRoot=Join-Path $qaRoot 'data'
New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $qaRoot 'desktop') -Force | Out-Null
$publicDesktop=[Environment]::GetFolderPath('CommonDesktopDirectory')
$fixture=Join-Path $publicDesktop ('ThemeStudio 权限验证 '+[Guid]::NewGuid().ToString('N').Substring(0,8)+'.lnk')
$profile=Join-Path $env:APPDATA 'com.seelen.seelen-ui\settings.json'
$profileExisted=Test-Path -LiteralPath $profile
$profileBackup=Join-Path $qaRoot 'seelen-settings-before.json'
if($profileExisted){Copy-Item -LiteralPath $profile -Destination $profileBackup}
$ownedProcessesBefore=@(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -like ((Join-Path $release 'runtimes\seelen')+'\*')})
if($ownedProcessesBefore.Count -gt 0){throw 'Owned Seelen runtime was already running; inspect it before this activation test.'}
$before=[ordered]@{time=(Get-Date -Format o);administrator=$true;wallpaper=(Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Desktop').Wallpaper;cursors=(Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Cursors' | Select-Object Arrow,Help,AppStarting,Wait,Crosshair,IBeam,NWPen,No,SizeNS,SizeWE,SizeNWSE,SizeNESW,SizeAll,UpArrow,Hand,Pin,Person);seelenProfileExisted=$profileExisted;fixture=$fixture}
$before | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $qaRoot 'before.json') -Encoding utf8
try{
    $shellObject=New-Object -ComObject WScript.Shell
    $link=$shellObject.CreateShortcut($fixture)
    $link.TargetPath=Join-Path $env:WINDIR 'System32\notepad.exe'
    $link.Description='Theme Studio bounded public-desktop permission test'
    $link.Save()
    $beforeHash=(Get-FileHash -LiteralPath $fixture).Hash
    @{extra_paths=@($fixture)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dataRoot 'settings.json') -Encoding utf8
    $image=[Drawing.Bitmap]::new(64,64)
    $graphics=[Drawing.Graphics]::FromImage($image)
    $graphics.Clear([Drawing.Color]::MediumSeaGreen)
    $imagePath=Join-Path $qaRoot '权限验证.png'
    $image.Save($imagePath,[Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose();$image.Dispose()
    $request=@{id=1;operation='icons.import';payload=@{name='权限验证.png';data=[Convert]::ToBase64String([IO.File]::ReadAllBytes($imagePath))}} | ConvertTo-Json -Depth 5 -Compress
    $importResponse=$request | & (Join-Path $release 'backend\ThemeStudio.Backend.exe') --data-dir $dataRoot --scan-dir (Join-Path $qaRoot 'desktop')
    if($LASTEXITCODE -ne 0 -or ($importResponse | ConvertFrom-Json).error){throw 'Public-desktop test picture preparation failed.'}
    $arguments=@('--smoke-dir',('"'+$qaRoot+'"'),'--qa-script',('"'+(Join-Path $projectRoot 'tools\qa-native-admin.js')+'"'))
    $app=Start-Process -FilePath (Join-Path $release 'ThemeStudio.exe') -ArgumentList $arguments -WindowStyle Hidden -PassThru
    if(-not $app.WaitForExit(150000)){throw 'Administrator native test timed out.'}
    $result=Get-Content -LiteralPath (Join-Path $qaRoot 'qa-result.json') -Raw | ConvertFrom-Json
    if((Get-FileHash -LiteralPath $fixture).Hash -cne $beforeHash){throw 'The public-desktop shortcut was not restored byte for byte.'}
    $result | Add-Member -NotePropertyName publicShortcutExactRestore -NotePropertyValue $true
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $qaRoot 'verified.json') -Encoding utf8
}catch{
    [pscustomobject]@{passed=$false;error=$_.Exception.Message;time=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaRoot 'driver-error.json') -Encoding utf8
}finally{
    $service=Join-Path $release 'runtimes\seelen\slu-service.exe'
    $seelenRoot=Join-Path $release 'runtimes\seelen'
    if(Test-Path -LiteralPath $service){& $service stop 2>$null}
    Start-Sleep -Milliseconds 800
    $owned=@(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -like ($seelenRoot+'\*')})
    foreach($ownedProcess in $owned){Stop-Process -Id $ownedProcess.ProcessId -Force -ErrorAction SilentlyContinue}
    $schedule=New-Object -ComObject 'Schedule.Service'
    $schedule.Connect()
    try{$task=$schedule.GetFolder('\Seelen').GetTask('Seelen UI Service');if([IO.Path]::GetFullPath($task.Definition.Actions.Item(1).Path) -ieq [IO.Path]::GetFullPath($service)){& $service uninstall 2>$null}}catch{}
    Start-Sleep -Milliseconds 500
    if($profileExisted){Copy-Item -LiteralPath $profileBackup -Destination $profile -Force}
    elseif(Test-Path -LiteralPath $profile){Remove-Item -LiteralPath $profile -Force}
    if(Test-Path -LiteralPath $fixture){
        $absolute=[IO.Path]::GetFullPath($fixture)
        if(-not $absolute.StartsWith([IO.Path]::GetFullPath($publicDesktop).TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture deletion escaped the public desktop.'}
        Remove-Item -LiteralPath $absolute -Force
    }
    $after=[ordered]@{time=(Get-Date -Format o);fixtureRemoved=(-not(Test-Path -LiteralPath $fixture));ownedSeelenProcessesRemaining=@(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -like ($seelenRoot+'\*')}).Count;seelenProfileRestored=if($profileExisted){(Get-FileHash -LiteralPath $profile).Hash -ceq (Get-FileHash -LiteralPath $profileBackup).Hash}else{-not(Test-Path -LiteralPath $profile)};wallpaper=(Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Desktop').Wallpaper}
    $after | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $qaRoot 'after.json') -Encoding utf8
}
