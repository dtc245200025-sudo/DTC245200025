$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskOutputDir = Join-Path $taskRoot 'outputs'
[IO.Directory]::CreateDirectory($taskOutputDir) | Out-Null
$taskOutputZip = Join-Path $taskOutputDir 'de32-chat-source.zip'
$taskFiles = @()
foreach ($taskDirectory in @('app','docs','nginx','postgres','scripts','tests','grafana','prometheus','loki','promtail')) {
    $taskFiles += Get-ChildItem -LiteralPath (Join-Path $taskRoot $taskDirectory) -File -Recurse |
        Where-Object { $_.FullName -notmatch '[\\/](__pycache__|\.pytest_cache)[\\/]' -and $_.Extension -notin @('.pyc','.pyo','.log') }
}
foreach ($taskName in @('.env.example','.gitattributes','.gitignore','AGENTS.md','MEMORY.md','README.md','compose.yml','compose.phase2.yml','compose.phase3.yml','pytest.ini')) {
    $taskFiles += Get-Item -Force -LiteralPath (Join-Path $taskRoot $taskName)
}
$taskStream = [IO.File]::Open($taskOutputZip, [IO.FileMode]::Create)
$taskArchive = [IO.Compression.ZipArchive]::new($taskStream, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($taskFile in $taskFiles) {
        $taskRelative = [IO.Path]::GetRelativePath($taskRoot, $taskFile.FullName).Replace('\','/')
        $taskEntry = $taskArchive.CreateEntry($taskRelative, [IO.Compression.CompressionLevel]::Optimal)
        $taskDestination = $taskEntry.Open()
        $taskSource = $taskFile.OpenRead()
        try { $taskSource.CopyTo($taskDestination) } finally { $taskSource.Dispose(); $taskDestination.Dispose() }
    }
} finally { $taskArchive.Dispose(); $taskStream.Dispose() }
Write-Output "SOURCE_ZIP_OK: $($taskFiles.Count) files; no .env/work/outputs/.git"
