param([ValidateSet('Create','Upload','Verify')][string]$Stage='Create')
$ErrorActionPreference='Stop'
$workspaceRoot='E:\desktop\windows'
$handoffRoot=Join-Path $workspaceRoot '.handoff'
$repository='yky0013/ThemeStudio'
$env:GIT_TERMINAL_PROMPT='0'
$env:GCM_INTERACTIVE='Never'
$credentialLines=@('protocol=https','host=github.com','','') | git credential fill
if($LASTEXITCODE -ne 0){throw 'GitHub authentication unavailable.'}
$credentialMap=@{}
foreach($credentialLine in $credentialLines){$parts=$credentialLine -split '=',2; if($parts.Length -eq 2){$credentialMap[$parts[0]]=$parts[1]}}
$headers=@{Authorization=('Bearer ' + $credentialMap['password']);Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28'}
$account=Invoke-RestMethod -Uri 'https://api.github.com/user' -Headers $headers -TimeoutSec 30
if($account.login -cne 'yky0013'){throw 'Unexpected GitHub account.'}
$releaseFile=Join-Path $handoffRoot 'github-release.json'
if($Stage -eq 'Create'){
    $commit=(git -C (Join-Path $workspaceRoot 'theme-studio') rev-parse HEAD).Trim()
    $body=@'
桌面主题工作室 0.1.1：Windows 10 2004+ / Windows 11，Intel/AMD x64。

安装包支持自选目录、中文路径、开始菜单、卸载和离线图文教程，并附带 Microsoft WebView2 离线运行库。图标和全局鼠标功能已在本机验证；壁纸视差当前属于设置页预览，完整桌面引擎和模组执行仍待接入。

源码标签对应安装包的原始构建提交。保留所有上游来源、许可证、固定提交和整合改动记录。

附加的 legacy-workspace 与 project-data 备份保存旧原型、研究/验证材料、原始 Git 元数据和清理前应用数据。本仓库为私有仓库。备份不需要安装，可供恢复开发或设置。
'@
    $release=Invoke-RestMethod -Method Post -Uri ('https://api.github.com/repos/' + $repository + '/releases') -Headers $headers -ContentType 'application/json' -Body (@{tag_name='v0.1.1';target_commitish=$commit;name='桌面主题工作室 0.1.1';body=$body;draft=$false;prerelease=$true} | ConvertTo-Json -Compress) -TimeoutSec 30
    $release | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $releaseFile -Encoding utf8
    [pscustomobject]@{Release=$release.html_url;Id=$release.id;Tag=$release.tag_name;Commit=$commit} | ConvertTo-Json
    return
}
$release=Get-Content -LiteralPath $releaseFile -Raw | ConvertFrom-Json
$backup=Get-Content -LiteralPath (Join-Path $handoffRoot 'backup-results.json') -Raw | ConvertFrom-Json
$files=@(
    (Join-Path $workspaceRoot 'theme-studio\installers\ThemeStudio-0.1.1-Windows-x64-Setup.exe'),
    (Join-Path $workspaceRoot 'theme-studio\installers\ThemeStudio-0.1.1-source.zip'),
    (Join-Path $workspaceRoot 'theme-studio\installers\SHA256.txt'),
    (Join-Path $workspaceRoot 'theme-studio\installers\release.json')
)
$files+=@($backup | ForEach-Object {Join-Path $handoffRoot $_.name})
$assetResponse=Invoke-RestMethod -Uri ('https://api.github.com/repos/' + $repository + '/releases/' + $release.id + '/assets') -Headers $headers -TimeoutSec 30
$assets=@($assetResponse)
$verification=@()
foreach($file in $files){
    $item=Get-Item -LiteralPath $file
    $hash=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    $asset=@($assets | Where-Object {$_.name -ceq $item.Name})
    if($asset.Count -eq 0 -and $Stage -eq 'Upload'){
        Add-Type -AssemblyName System.Net.Http
        $client=[System.Net.Http.HttpClient]::new()
        $client.Timeout=[TimeSpan]::FromMinutes(20)
        $client.DefaultRequestHeaders.Authorization=[System.Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$credentialMap['password'])
        $client.DefaultRequestHeaders.UserAgent.ParseAdd('ThemeStudio-Handoff/0.1.1')
        $client.DefaultRequestHeaders.Add('X-GitHub-Api-Version','2022-11-28')
        $stream=[IO.File]::OpenRead($item.FullName)
        $content=[System.Net.Http.StreamContent]::new($stream)
        $content.Headers.ContentType=[System.Net.Http.Headers.MediaTypeHeaderValue]::new('application/octet-stream')
        $url=($release.upload_url -replace '\{.*$','') + '?name=' + [Uri]::EscapeDataString($item.Name)
        try{
            Write-Output ('Uploading ' + $item.Name + ' (' + $item.Length + ' bytes)')
            $response=$client.PostAsync($url,$content).GetAwaiter().GetResult()
            if(-not $response.IsSuccessStatusCode){throw ('GitHub upload failed with HTTP ' + [int]$response.StatusCode)}
            $uploaded=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
            $asset=@($uploaded)
            $assets+=@($uploaded)
        } finally {$content.Dispose();$stream.Dispose();$client.Dispose()}
    }
    if($asset.Count -ne 1 -or $asset[0].state -ne 'uploaded' -or $asset[0].size -ne $item.Length){throw ('Uploaded asset is absent or size mismatched: ' + $item.Name)}
    $digest='sha256:' + $hash
    if($asset[0].digest -cne $digest){throw ('Uploaded asset SHA-256 is absent or mismatched: ' + $item.Name)}
    $verification+=@([pscustomobject]@{name=$item.Name;bytes=$item.Length;sha256=$hash;remoteDigest=$asset[0].digest;url=$asset[0].browser_download_url;verified=$true})
    Write-Output ('Verified ' + $item.Name)
}
$verification | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $handoffRoot 'github-assets-verified.json') -Encoding utf8
[pscustomobject]@{Release=$release.html_url;AssetsVerified=$verification.Count} | ConvertTo-Json
