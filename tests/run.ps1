$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$runtime = (Get-Command calibre-debug.exe -ErrorAction Stop).Source
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('isfdb4-tests-' + [guid]::NewGuid())
$keys = @('CALIBRE_CONFIG_DIRECTORY','CALIBRE_CACHE_DIRECTORY','CALIBRE_TEMP_DIR','TEMP','TMP','PYTHONDONTWRITEBYTECODE','CALIBRE_OVERRIDE_LANG','ISFDB4_TEST_ROOT','CALIBRE_DEVELOP_FROM')
$saved = @{}
foreach ($key in $keys) { $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
try {
    New-Item -ItemType Directory -Path $scratch | Out-Null
    foreach ($name in @('config','cache','temp')) { New-Item -ItemType Directory -Path (Join-Path $scratch $name) | Out-Null }
    $env:CALIBRE_CONFIG_DIRECTORY = Join-Path $scratch 'config'
    $env:CALIBRE_CACHE_DIRECTORY = Join-Path $scratch 'cache'
    $env:CALIBRE_TEMP_DIR = Join-Path $scratch 'temp'
    $env:TEMP = $env:CALIBRE_TEMP_DIR
    $env:TMP = $env:CALIBRE_TEMP_DIR
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:CALIBRE_OVERRIDE_LANG = 'en'
    $env:ISFDB4_TEST_ROOT = $scratch
    Remove-Item Env:CALIBRE_DEVELOP_FROM -ErrorAction SilentlyContinue
    & $runtime -e (Join-Path $PSScriptRoot 'run_calibre.py')
    $result = $LASTEXITCODE
} finally {
    foreach ($key in $keys) { [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process') }
    $resolved = [IO.Path]::GetFullPath($scratch)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($resolved.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolved -Leaf).StartsWith('isfdb4-tests-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    } else { throw 'Refusing cleanup outside the generated temporary directory' }
}
exit $result
