"""Compile a theme into a PowerShell prompt function with PSReadLine options."""

from __future__ import annotations

from ..colors import name_for_sgr, powershell_color
from ..config import Theme

__all__ = ["name", "render"]

name = "pwsh"

RAW = {
    "user": "$env:USERNAME",
    "host": "$env:COMPUTERNAME",
    "dir": "& __j_pwd",
    "git": "& __j_git_branch",
    "git_state": "& __j_git_state",
    "venv": "& __j_venv",
    "time": "& __j_time",
    "exit_code": "& __j_exit_code",
}

FUNCTIONS = """$__j_default_color = if ($PSVersionTable.PSVersion.Major -ge 7) { [Console]::ForegroundColor } else { [Console]::Color }

function __j_set_color([object]$color) {
    if ($PSVersionTable.PSVersion.Major -ge 7) {
        if ($color -ne '') { [Console]::ForegroundColor = $color } else { [Console]::ForegroundColor = $__j_default_color }
    } else {
        if ($color -ne '') { [Console]::Color = $color } else { [Console]::Color = $__j_default_color }
    }
}

function __j_seg([object]$color, [object]$value) {
    if ($null -eq $value -or $value -eq '') { return }
    __j_set_color $color
    Write-Host "$value" -NoNewline
}

function __j_seg_ansi([string]$sgr, [object]$value) {
    if ($null -eq $value -or $value -eq '') { return }
    $escape = [char]27
    Write-Host ($escape + '[' + $sgr + 'm' + "$value" + $escape + '[0m') -NoNewline
}

function __j_sep([string]$text) {
    if ($text -eq '') { return }
    __j_set_color ''
    Write-Host $text -NoNewline
}

function __j_pwd {
    $path = (Get-Location).Path
    $home = $env:HOME
    if ($null -eq $home -or $home -eq '') { $home = $env:USERPROFILE }
    if ($null -eq $home -or $home -eq '') { return $path }
    $home = $home.TrimEnd('/')
    if ($path -eq $home) { return '~' }
    if ($path.StartsWith($home + '/')) { return '~' + $path.Substring($home.Length) }
    return $path
}

function __j_git_branch { git rev-parse --abbrev-ref HEAD 2>$null }

function __j_git_state {
    $status = git status --porcelain=v1 2>$null
    if (-not $status) { return '' }
    $state = '*'
    if (($status | Where-Object { $_.Length -ge 3 -and $_.Substring(0, 3) -eq '?? ' }).Count -gt 0) { $state = "${state}+" }
    return $state
}

function __j_venv {
    if ($env:VIRTUAL_ENV) { [System.IO.Path]::GetFileName($env:VIRTUAL_ENV) }
    elseif ($env:CONDA_PREFIX) { [System.IO.Path]::GetFileName($env:CONDA_PREFIX) }
}

function __j_time { (Get-Date).ToString('HH:mm') }

function __j_exit_code { if ($__j_last_exit -ne 0) { return "x$__j_last_exit" } }

"""


def _quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _calls(theme: Theme) -> list[str]:
    calls: list[str] = ["    $__j_last_exit = $LASTEXITCODE"]
    for index, segment in enumerate(list(theme.prompt) + list(theme.status)):
        raw = RAW.get(segment)
        if not raw:
            continue
        if index:
            calls.append(f"    __j_sep {_quote(theme.separator)}")
        sgr = theme.color(segment)
        named = powershell_color(theme.palette_spec(segment) or name_for_sgr(sgr))
        if sgr and named:
            calls.append(f"    __j_seg [ConsoleColor]::{named} {raw}")
        elif sgr:
            calls.append(f"    __j_seg_ansi {_quote(sgr)} {raw}")
        else:
            calls.append(f"    __j_seg '' {raw}")
    return calls


def render(theme: Theme) -> str:
    """Return a self-contained PowerShell block that redefines the prompt."""
    body = "\n".join(_calls(theme))
    script = FUNCTIONS
    script += "if (Get-Command -Name Set-PSReadLineOption -ErrorAction SilentlyContinue) {\n"
    script += "    Set-PSReadLineOption -PromptText ''\n}\n\n"
    script += "function prompt {\n"
    script += body + "\n"
    script += "    __j_set_color ''\n"
    script += "    ''\n}\n"
    return script
