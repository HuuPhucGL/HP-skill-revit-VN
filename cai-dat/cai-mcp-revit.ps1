<#
Ten script : cai-mcp-revit.ps1
Cong dung  : Cai ket noi Claude <-> Revit (mcp-servers-for-revit v1.0.0, ma nguon mo MIT)
             1. Tai Node 22 ban roi (portable) vao %LOCALAPPDATA%\HP-RevitMCP\node22 (kiem tra SHA256)
             2. Cai MCP server "mcp-server-for-revit" vao %LOCALAPPDATA%\HP-RevitMCP\server
             3. Tai plugin Revit dung phien ban, chep vao %APPDATA%\Autodesk\Revit\Addins\<nam>
             4. Dang ky MCP server "revit" vao Claude Code (~/.claude.json), co sao luu truoc
             5. (Tuy chon) Dang ky them vao Claude Desktop, chep bo skill vao ~/.claude/skills
Cach dung  : Mo PowerShell, chay:
               powershell -ExecutionPolicy Bypass -File .\cai-mcp-revit.ps1 -RevitVersion 2024
             Them -ClaudeDesktop de dang ky cho Claude Desktop, -CaiSkill de chep skill.
Ngay viet  : 2026-11-10
Ghi chu    : Dung Node 22 vi thu vien better-sqlite3 cua server chua co ban dung san cho Node moi hon.
             Script KHONG tat plugin khac. Neu may co plugin khac chiem cong 8080 thi script chi canh bao.
#>
param(
    [ValidateSet("2020", "2021", "2022", "2023", "2024", "2025", "2026")]
    [string]$RevitVersion = "2024",
    [switch]$ClaudeDesktop,
    [switch]$CaiSkill
)
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Goc       = Join-Path $env:LOCALAPPDATA "HP-RevitMCP"
$NodeDir   = Join-Path $Goc "node22"
$ServerDir = Join-Path $Goc "server"
$AddinDir  = Join-Path $env:APPDATA "Autodesk\Revit\Addins\$RevitVersion"
$PluginTag = "v1.0.0"
$Tam       = Join-Path $env:TEMP ("hp-revitmcp-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $Goc, $Tam | Out-Null

function Buoc($s) { Write-Host "`n==> $s" -ForegroundColor Cyan }

if (Get-Process Revit -ErrorAction SilentlyContinue) {
    throw "Revit dang mo. Hay dong Revit roi chay lai script (de chep duoc file plugin)."
}

# ---------------------------------------------------------------- 1. Node 22
Buoc "1/5 Node 22 ban roi"
$NodeExe = Join-Path $NodeDir "node.exe"
if (Test-Path $NodeExe) {
    Write-Host "Da co: $(& $NodeExe -v)"
} else {
    $ds = Invoke-RestMethod "https://nodejs.org/dist/index.json"
    $ver = ($ds | Where-Object { $_.version -like "v22.*" } | Select-Object -First 1).version
    $zip = "node-$ver-win-x64.zip"
    $zipPath = Join-Path $Tam $zip
    Invoke-WebRequest "https://nodejs.org/dist/$ver/$zip" -OutFile $zipPath -UseBasicParsing
    $sums = (Invoke-WebRequest "https://nodejs.org/dist/$ver/SHASUMS256.txt" -UseBasicParsing).Content
    $mong = (($sums -split "`n") | Where-Object { $_ -match [regex]::Escape($zip) + '$' }) -split '\s+' | Select-Object -First 1
    $thuc = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower()
    if ($mong -ne $thuc) { throw "Sai ma SHA256 cua $zip. Dung cai dat." }
    Expand-Archive $zipPath -DestinationPath $Tam -Force
    Move-Item (Join-Path $Tam "node-$ver-win-x64") $NodeDir
    Write-Host "Da cai Node $ver"
}

# ---------------------------------------------------------------- 2. MCP server
Buoc "2/5 MCP server mcp-server-for-revit"
New-Item -ItemType Directory -Force $ServerDir | Out-Null
$pkg = Join-Path $ServerDir "package.json"
if (-not (Test-Path $pkg)) { '{"name":"hp-revit-mcp-host","private":true}' | Out-File -Encoding ascii $pkg }
$env:Path = "$NodeDir;" + $env:Path
Push-Location $ServerDir
try {
    & (Join-Path $NodeDir "npm.cmd") install "mcp-server-for-revit@1.0.0" --no-fund --no-audit --loglevel=error
    if ($LASTEXITCODE -ne 0) { throw "npm install that bai" }
} finally { Pop-Location }
$ServerJs = Join-Path $ServerDir "node_modules\mcp-server-for-revit\build\index.js"
if (-not (Test-Path $ServerJs)) { throw "Khong thay $ServerJs" }
Write-Host "Server: $ServerJs"

# ---------------------------------------------------------------- 3. Plugin Revit
Buoc "3/5 Plugin cho Revit $RevitVersion"
$rel = "mcp-servers-for-revit-$PluginTag-Revit$RevitVersion.zip"
$relPath = Join-Path $Tam $rel
Invoke-WebRequest "https://github.com/mcp-servers-for-revit/mcp-servers-for-revit/releases/download/$PluginTag/$rel" -OutFile $relPath -UseBasicParsing
$giai = Join-Path $Tam "plugin"
Expand-Archive $relPath -DestinationPath $giai -Force
New-Item -ItemType Directory -Force $AddinDir | Out-Null
# Goi co 2 file .addin trung ClientId: chi chep 1 file de Revit khong bao trung
Copy-Item (Join-Path $giai "mcp-servers-for-revit.addin") $AddinDir -Force
Copy-Item (Join-Path $giai "revit_mcp_plugin") $AddinDir -Recurse -Force
Get-ChildItem (Join-Path $AddinDir "revit_mcp_plugin") -Recurse -File | Unblock-File
Write-Host "Da chep plugin vao $AddinDir"
$khac = Get-ChildItem $AddinDir -Filter *.addin | Where-Object { $_.Name -notin @("mcp-servers-for-revit.addin") } |
    Where-Object { (Get-Content $_.FullName -Raw) -match "MCP|8080" }
foreach ($k in $khac) {
    Write-Warning "Co plugin khac co the chiem cong 8080: $($k.FullName). Neu ket noi loi, hay tam tat plugin nay."
}

# ---------------------------------------------------------------- 4. Dang ky voi Claude
Buoc "4/5 Dang ky MCP server 'revit'"
$dangKy = @'
const fs = require("fs");
const [file, cmd, js] = process.argv.slice(2);
let d = {};
if (fs.existsSync(file)) {
  fs.copyFileSync(file, file + ".bak-" + new Date().toISOString().slice(0, 10));
  d = JSON.parse(fs.readFileSync(file, "utf8"));
}
d.mcpServers = d.mcpServers || {};
d.mcpServers.revit = { type: "stdio", command: cmd, args: [js], env: {} };
fs.writeFileSync(file, JSON.stringify(d, null, 2));
console.log("Da ghi: " + file);
'@
$jsFile = Join-Path $Tam "dangky.js"
$dangKy | Out-File -Encoding ascii $jsFile
& $NodeExe $jsFile (Join-Path $env:USERPROFILE ".claude.json") $NodeExe $ServerJs
if ($ClaudeDesktop) {
    $cd = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
    New-Item -ItemType Directory -Force (Split-Path $cd) | Out-Null
    & $NodeExe $jsFile $cd $NodeExe $ServerJs
}

# ---------------------------------------------------------------- 5. Skill
Buoc "5/5 Bo skill"
if ($CaiSkill) {
    $nguon = Join-Path (Split-Path $PSScriptRoot) "skills"
    $dich = Join-Path $env:USERPROFILE ".claude\skills"
    New-Item -ItemType Directory -Force $dich | Out-Null
    Get-ChildItem $nguon -Directory | ForEach-Object { Copy-Item $_.FullName $dich -Recurse -Force; Write-Host "Skill: $($_.Name)" }
} else {
    Write-Host "Bo qua (them -CaiSkill de chep skill vao ~/.claude/skills)"
}

Remove-Item $Tam -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "`nXONG. Viec tiep theo:" -ForegroundColor Green
Write-Host " 1. Mo Revit $RevitVersion, neu hoi plugin la thi bam 'Always Load'."
Write-Host " 2. Tab Add-Ins > Revit MCP Plugin > Settings: tich cac lenh can dung > Save."
Write-Host " 3. Bam 'Revit MCP Switch' de bat ket noi."
Write-Host " 4. Khoi dong lai Claude Code / Claude Desktop."
