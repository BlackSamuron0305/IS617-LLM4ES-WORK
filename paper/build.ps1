#Requires -Version 5.1
<#
.SYNOPSIS
    Compile paper.pdf and clean up every build artifact afterwards.

.DESCRIPTION
    Runs latexmk (pdflatex + bibtex, as many passes as needed), then
    deletes everything in this folder that is not a source file or the
    finished PDF.

    Artifacts are removed by EXCLUSION: anything whose extension is not
    in $Keep gets deleted. That means a new artifact type never needs
    the script updated -- but it also means $Keep must stay correct.

    acl.sty and acl_natbib.bst are REQUIRED to compile. They are not
    artifacts. Do not remove them from $Keep.

    If the compile fails, nothing is cleaned, so paper.log survives for
    you to read.

.PARAMETER Main
    Base name of the document. Defaults to 'paper'.

.PARAMETER DryRun
    Compile, then list what would be deleted without deleting it.

.PARAMETER NoClean
    Compile and keep all artifacts.

.EXAMPLE
    .\build.ps1
.EXAMPLE
    .\build.ps1 -DryRun
#>
[CmdletBinding()]
param(
    [string]$Main = 'paper',
    [switch]$DryRun,
    [switch]$NoClean
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

# Extensions that survive the clean. Everything else in this folder is
# treated as a build artifact and deleted.
#   .tex .bib          our sources
#   .pdf               the output (and any figure PDFs)
#   .sty .bst .cls     the ACL template -- REQUIRED TO COMPILE
#   .md                the template's documentation
#   .png .jpg .eps     figures
#   .ps1 .gitignore    this script, and git config
$Keep = @(
    '.tex', '.bib', '.pdf',
    '.sty', '.bst', '.cls',
    '.md',
    '.png', '.jpg', '.jpeg', '.eps',
    '.ps1', '.gitignore'
)

# Page limit for the IS 617 report; the script warns if we exceed it.
$PageLimit = 5

if (-not (Test-Path -LiteralPath "$Main.tex")) {
    throw "$Main.tex not found in $PSScriptRoot"
}
if (-not (Get-Command latexmk -ErrorAction SilentlyContinue)) {
    throw 'latexmk is not on PATH. Install TeX Live, or add its bin directory to PATH.'
}

Write-Host "Compiling $Main.tex ..." -ForegroundColor Cyan

$output = & latexmk -pdf -interaction=nonstopmode -halt-on-error "$Main.tex" 2>&1
$compiled = ($LASTEXITCODE -eq 0)

if (-not $compiled) {
    Write-Host ''
    Write-Host 'COMPILE FAILED. Artifacts kept so you can read the log.' -ForegroundColor Red
    Write-Host ''
    $output | Select-String -Pattern '^!|^l\.\d|LaTeX Error|Emergency stop' |
        Select-Object -First 15 |
        ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Write-Host ''
    Write-Host "  Full log: $(Join-Path $PSScriptRoot "$Main.log")" -ForegroundColor DarkGray
    exit 1
}

# --- report before the log is deleted ---------------------------------

$pages = $null
$written = $output | Select-String -Pattern 'Output written on .*\((\d+) pages?' | Select-Object -Last 1
if ($written) { $pages = [int]$written.Matches[0].Groups[1].Value }

Write-Host "Built $Main.pdf" -ForegroundColor Green
if ($pages) {
    if ($pages -gt $PageLimit) {
        Write-Host "  $pages pages -- OVER the $PageLimit-page limit" -ForegroundColor Yellow
    } else {
        Write-Host "  $pages pages (limit $PageLimit)" -ForegroundColor DarkGray
    }
}

# Undefined citations are easy to miss and the log is about to go.
if (Test-Path -LiteralPath "$Main.log") {
    $undef = Select-String -LiteralPath "$Main.log" -Pattern "Citation '([^']+)' (on page \d+ )?undefined" -AllMatches
    if ($undef) {
        $keys = $undef.Matches | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
        Write-Host "  UNDEFINED CITATIONS: $($keys -join ', ')" -ForegroundColor Yellow
        Write-Host '  (add them to custom.bib -- verify against Crossref/arXiv first)' -ForegroundColor DarkGray
    }
}

if ($NoClean) {
    Write-Host 'Artifacts kept (-NoClean).' -ForegroundColor DarkGray
    exit 0
}

# --- clean -------------------------------------------------------------

$junk = Get-ChildItem -LiteralPath $PSScriptRoot -File -Force |
    Where-Object { $Keep -notcontains $_.Extension.ToLower() }

if (-not $junk) {
    Write-Host 'Nothing to clean.' -ForegroundColor DarkGray
    exit 0
}

if ($DryRun) {
    Write-Host "Would delete $($junk.Count) file(s):" -ForegroundColor Yellow
    $junk | ForEach-Object { Write-Host "  $($_.Name)" }
    exit 0
}

foreach ($f in $junk) {
    try {
        Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
    } catch {
        Write-Host "  could not delete $($f.Name): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
Write-Host "Cleaned $($junk.Count) artifact(s)." -ForegroundColor DarkGray
