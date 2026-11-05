$ErrorActionPreference = 'Stop'
$runtime = (Get-Command calibre-debug.exe -ErrorAction Stop).Source
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('isfdb4-feasibility-' + [guid]::NewGuid())
$keys = @('CALIBRE_CONFIG_DIRECTORY','CALIBRE_CACHE_DIRECTORY','CALIBRE_TEMP_DIR','TEMP','TMP','PYTHONDONTWRITEBYTECODE','CALIBRE_OVERRIDE_LANG','ISFDB4_FEASIBILITY_ROOT','CALIBRE_DEVELOP_FROM','CALIBRE_METADATA_BROWSER_WORKER')
$saved = @{}
foreach ($key in $keys) { $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
try {
    foreach ($name in @('config','cache','temp')) { New-Item -ItemType Directory -Path (Join-Path $scratch $name) -Force | Out-Null }
    $env:CALIBRE_CONFIG_DIRECTORY = Join-Path $scratch 'config'
    $env:CALIBRE_CACHE_DIRECTORY = Join-Path $scratch 'cache'
    $env:CALIBRE_TEMP_DIR = Join-Path $scratch 'temp'
    $env:TEMP = $env:CALIBRE_TEMP_DIR
    $env:TMP = $env:CALIBRE_TEMP_DIR
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:CALIBRE_OVERRIDE_LANG = 'en'
    $env:ISFDB4_FEASIBILITY_ROOT = $scratch
    Remove-Item Env:CALIBRE_DEVELOP_FROM -ErrorAction SilentlyContinue
    Remove-Item Env:CALIBRE_METADATA_BROWSER_WORKER -ErrorAction SilentlyContinue
    & $runtime -e (Join-Path $PSScriptRoot 'camoufox_feasibility.py')
    $result = $LASTEXITCODE
} finally {
    foreach ($key in $keys) { [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process') }
    $resolved = [IO.Path]::GetFullPath($scratch)
    if ($resolved.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()), [StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolved -Leaf).StartsWith('isfdb4-feasibility-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    } else { throw 'Refusing cleanup outside the generated temporary directory' }
}
exit $result
