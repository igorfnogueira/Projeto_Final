# Bootstrap Idempotente e Determinístico de Governança
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = Get-Location }

$repoRoot = git -C $scriptDir rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = $scriptDir }

$currentHooks = git -C $repoRoot config --get core.hooksPath 2>$null

if ($currentHooks -ne ".githooks") {
    git -C $repoRoot config core.hooksPath .githooks
    
    if ((git -C $repoRoot config --get core.hooksPath) -eq ".githooks") {
        Write-Host "[governanca] Hooks ativados com sucesso (.githooks)." -ForegroundColor Green
        $logDir = Join-Path $repoRoot ".githooks"
        if (Test-Path $logDir) {
            $logEntry = "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) | core.hooksPath configurado para .githooks"
            Add-Content -Path (Join-Path $logDir ".setup.log") -Value $logEntry -Encoding UTF8 -Force
        }
    }
}

$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) {
    $pluginErro = claude plugin install mattpocock-skills@claude-plugins-official --scope project --yes 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[governanca] Plugin mattpocock-skills habilitado (--scope project)." -ForegroundColor Green
    } else {
        Write-Host "[governanca] Falha ao instalar o plugin mattpocock-skills (saida $LASTEXITCODE). Rode manualmente depois: claude plugin install mattpocock-skills@claude-plugins-official --scope project" -ForegroundColor Yellow
        Write-Host "  $pluginErro" -ForegroundColor Yellow
    }
} else {
    Write-Host "[governanca] CLI 'claude' nao encontrado no PATH -- pulei a instalacao do plugin mattpocock-skills. Rode manualmente depois: claude plugin install mattpocock-skills@claude-plugins-official --scope project" -ForegroundColor Yellow
}