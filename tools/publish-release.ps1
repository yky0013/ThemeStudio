param([ValidateSet('Create','Upload','Verify')][string]$Stage='Verify')
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$repository = 'yky0013/ThemeStudio'
$version = (Get-Content -LiteralPath (Join-Path $projectRoot 'package.json') -Raw | ConvertFrom-Json).version
$tag = 'v' + $version
$releaseDirectory = Join-Path $projectRoot 'installers'
$releaseFile = Join-Path $releaseDirectory 'github-release.json'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'Never'
$credentialLines = @('protocol=https','host=github.com','','') | git credential fill
if ($LASTEXITCODE -ne 0) { throw 'GitHub authentication unavailable.' }
$credentialMap = @{}
foreach ($line in $credentialLines) { $parts = $line -split '=',2; if ($parts.Length -eq 2) { $credentialMap[$parts[0]] = $parts[1] } }
$headers = @{Authorization=('Bearer ' + $credentialMap['password']);Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28'}
$account = Invoke-RestMethod -Uri 'https://api.github.com/user' -Headers $headers -TimeoutSec 30
if ($account.login -cne 'yky0013') { throw 'Unexpected GitHub account.' }
if ($Stage -eq 'Create') {
    $commit = (git -C $projectRoot rev-parse HEAD).Trim()
    $body = @'
桌面主题工作室 0.2.0，Windows 10 2004+ / Windows 11，Intel/AMD x64。

安装和启动申请管理员权限；桌面快捷方式与图片逐项对应；图片/视频和鼠标视差应用到真实桌面；启用用户选定的 Seelen Dock 与工具栏；Windhawk 使用匹配版本的原始离线编译器和 CLI 编译、启用与停用本地模组。

已在本机验证公共桌面图标替换与原样恢复、两项目独立图片配对、真实图片/视频背景播放与停止、Seelen 启用与停止，以及 Windhawk mouse-trail DLL 实际载入。20 个前端测试与 31 个 Windows 后端测试通过。其他模组和物理多显示器环境未逐一验证。

安装包包含 WebView2 离线运行库和原始引擎/编译工具；卸载停止工作室运行组件，保留用户素材及图标/指针备份。源码保留上游许可证、固定提交、完整对应源码和本地集成记录。此仓库为私有仓库。
'@
    $release = Invoke-RestMethod -Method Post -Uri ('https://api.github.com/repos/' + $repository + '/releases') -Headers $headers -ContentType 'application/json' -Body (@{tag_name=$tag;target_commitish=$commit;name=('桌面主题工作室 ' + $version);body=$body;draft=$false;prerelease=$true} | ConvertTo-Json -Compress) -TimeoutSec 30
    $release | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $releaseFile -Encoding utf8
    [pscustomobject]@{release=$release.html_url;id=$release.id;tag=$release.tag_name;commit=$commit} | ConvertTo-Json
    return
}
$release = Get-Content -LiteralPath $releaseFile -Raw | ConvertFrom-Json
if ($release.tag_name -cne $tag) { throw 'Saved release tag does not match this version.' }
$assetResponse = Invoke-RestMethod -Uri ('https://api.github.com/repos/' + $repository + '/releases/' + $release.id + '/assets') -Headers $headers -TimeoutSec 30
$assets = @($assetResponse)
$files = @(('ThemeStudio-' + $version + '-Windows-x64-Setup.exe'), ('ThemeStudio-' + $version + '-source.zip'), 'SHA256.txt', 'release.json')
$verification = @()
Add-Type -AssemblyName System.Net.Http
foreach ($name in $files) {
    $item = Get-Item -LiteralPath (Join-Path $releaseDirectory $name)
    $hash = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $asset = @($assets | Where-Object {$_.name -ceq $item.Name})
    if ($asset.Count -eq 0 -and $Stage -eq 'Upload') {
        $client = [System.Net.Http.HttpClient]::new()
        $client.Timeout = [TimeSpan]::FromMinutes(20)
        $client.DefaultRequestHeaders.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$credentialMap['password'])
        $client.DefaultRequestHeaders.UserAgent.ParseAdd('ThemeStudio-Release/' + $version)
        $client.DefaultRequestHeaders.Add('X-GitHub-Api-Version','2022-11-28')
        $stream = [IO.File]::OpenRead($item.FullName)
        $content = [System.Net.Http.StreamContent]::new($stream)
        $content.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::new('application/octet-stream')
        $url = ($release.upload_url -replace '\{.*$','') + '?name=' + [Uri]::EscapeDataString($item.Name)
        try {
            Write-Output ('Uploading ' + $item.Name + ' (' + $item.Length + ' bytes)')
            $response = $client.PostAsync($url,$content).GetAwaiter().GetResult()
            if (-not $response.IsSuccessStatusCode) { throw ('GitHub upload failed with HTTP ' + [int]$response.StatusCode) }
            $uploaded = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
            $asset = @($uploaded)
            $assets += @($uploaded)
        } finally { $content.Dispose(); $stream.Dispose(); $client.Dispose() }
    }
    if ($asset.Count -ne 1 -or $asset[0].state -ne 'uploaded' -or $asset[0].size -ne $item.Length -or $asset[0].digest -cne ('sha256:' + $hash)) { throw ('Uploaded asset verification failed: ' + $item.Name) }
    $verification += @([pscustomobject]@{name=$item.Name;bytes=$item.Length;sha256=$hash;remoteDigest=$asset[0].digest;url=$asset[0].browser_download_url;verified=$true})
    Write-Output ('Verified ' + $item.Name)
}
$verification | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $releaseDirectory 'github-assets-verified.json') -Encoding utf8
[pscustomobject]@{release=$release.html_url;assetsVerified=$verification.Count} | ConvertTo-Json
