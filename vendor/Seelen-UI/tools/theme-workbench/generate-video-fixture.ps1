$ErrorActionPreference = 'Stop'
$videoFixture = Join-Path $PSScriptRoot '..\..\src\ui\react\settings\public\fixtures\parallax-motion.mp4'
if (Test-Path -LiteralPath $videoFixture) { throw 'Fixture already exists; preserve it or choose a new output explicitly.' }
& ffmpeg -hide_banner -loglevel error -f lavfi -i 'testsrc2=size=960x540:rate=24:duration=12' -an -c:v libx264 -preset fast -crf 28 -pix_fmt yuv420p -movflags +faststart -n $videoFixture
if ($LASTEXITCODE -ne 0) { throw 'Video fixture generation failed.' }
