# Understudy one-command bootstrap for Windows PowerShell. Read me first — I'm short.
#
#   irm https://raw.githubusercontent.com/Ali-Ahmad-Khan/understudy/main/setup.ps1 | iex                       # per-project, current dir
#   & ([scriptblock]::Create((irm .../setup.ps1))) global                                                      # machine-wide
#   & ([scriptblock]::Create((irm .../setup.ps1))) cursor C:\code\my-app   # targets: claude|global|cursor|agents|prompt
#
# Mirrors setup.sh: (1) fetch the kit once into %LOCALAPPDATA%\understudy
# (git clone if available, zip download otherwise), (2) run install.py, which
# writes ONLY inside the target project — no global agent config is touched.
# Overrides: UNDERSTUDY_REPO (source URL), UNDERSTUDY_HOME (cache dir).
param(
    [string]$Target = "claude",
    [string]$Dest = ".",
    [switch]$Force
)
$ErrorActionPreference = "Stop"

$Repo = if ($env:UNDERSTUDY_REPO) { $env:UNDERSTUDY_REPO } else { "https://github.com/Ali-Ahmad-Khan/understudy" }
$Kit  = if ($env:UNDERSTUDY_HOME) { $env:UNDERSTUDY_HOME } else { Join-Path $env:LOCALAPPDATA "understudy" }

if (Test-Path (Join-Path $Kit ".git")) {
    try { git -C $Kit pull --ff-only --quiet } catch { Write-Warning "could not update $Kit — using existing copy" }
} elseif (-not (Test-Path (Join-Path $Kit "install.py"))) {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        git clone --depth 1 --quiet $Repo $Kit
    } else {
        $zip = Join-Path ([System.IO.Path]::GetTempPath()) "understudy.zip"
        $extract = Join-Path ([System.IO.Path]::GetTempPath()) "understudy-extract"
        Invoke-WebRequest "$Repo/archive/refs/heads/main.zip" -OutFile $zip
        Expand-Archive $zip -DestinationPath $extract -Force
        New-Item -ItemType Directory -Force -Path $Kit | Out-Null
        Copy-Item (Join-Path $extract "understudy-main\*") $Kit -Recurse -Force
        Remove-Item $zip; Remove-Item $extract -Recurse
    }
}
if (-not (Test-Path (Join-Path $Kit "install.py"))) { throw "setup: fetch failed — $Kit has no install.py" }

$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" }
      elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" }
      else { throw "Python 3 is required (https://python.org — check 'Add to PATH')" }

$installArgs = @($Target, $Dest)
if ($Force) { $installArgs += "--force" }
& $py (Join-Path $Kit "install.py") @installArgs
