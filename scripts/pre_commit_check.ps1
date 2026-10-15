# pre_commit_check.ps1 — Pre-commit gate check entry (T3-13, 2026-09-04 user decision landing)
#
# Invokes scripts/validate_audit.py --stack auto and passes through the exit code;
# no .github/ workflow is created. Whether to wire it into git hooks is up to the
# user (e.g. after `git config core.hooksPath <dir>`, call this script in that
# directory's pre-commit, or append it to the existing .git/hooks/pre-commit).
#
# Usage:
#   .\scripts\pre_commit_check.ps1                        # Validate the self-test samples by default (regression baseline)
#   .\scripts\pre_commit_check.ps1 <audit_output_dir>     # Validate the specified audit output directory
#
# Exit code semantics (same as validate_audit.py):
#   0 = passed / WARN only (allowed)
#   1 = FAIL exists (blocks the commit)
#   2 = usage error / environment missing

param(
    [string]$Target = "scripts/_demo_audit"
)

$ErrorActionPreference = "Stop"
$repoRoot  = Split-Path -Parent $PSScriptRoot
$validator = Join-Path $PSScriptRoot "validate_audit.py"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "[pre-commit] python not found; please install Python 3.8+ first"
    exit 2
}
if (-not (Test-Path $validator)) {
    Write-Error "[pre-commit] Gate script not found: $validator"
    exit 2
}
if (-not (Test-Path (Join-Path $repoRoot $Target))) {
    Write-Error "[pre-commit] Target directory does not exist: $Target"
    exit 2
}

Push-Location $repoRoot
try {
    python $validator $Target --stack auto
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}

# Pass through the exit code; the caller (git hook / CI / human) makes the decision
exit $code
