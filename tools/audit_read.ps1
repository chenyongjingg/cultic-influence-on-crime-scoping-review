<#
  Read the 30 flagged records, one at a time, and record a verdict.

  Usage (from the local/ folder):
      powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_read.ps1
      powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_read.ps1 -Start 12
      powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_read.ps1 -Index

  Progress is saved after every record: close the window and re-run to continue
  where you stopped. Verdicts go to out\supplements\S10_verdicts.csv, a small
  side file; the worksheet itself is never rewritten, so the abstracts cannot be
  damaged by a round-trip through the console encoding.
#>

param(
    [int]$Start = 0,
    [switch]$Index
)

$ErrorActionPreference = "Stop"

try { chcp 65001 > $null } catch {}
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$Root  = Split-Path -Parent $PSScriptRoot
$Form  = Join-Path $Root "out\supplements\S10_human_audit.csv"
$Side  = Join-Path $Root "out\supplements\S10_verdicts.csv"

if (-not (Test-Path $Form)) { Write-Host "missing form: $Form" -ForegroundColor Red; exit 1 }

$rows = Import-Csv -Path $Form -Encoding UTF8

# ---- existing verdicts ------------------------------------------------------
$done = @{}
if (Test-Path $Side) {
    Import-Csv -Path $Side -Encoding UTF8 | ForEach-Object {
        if ($_.id) { $done[$_.id] = $_.verdict }
    }
}

if ($Index) {
    $n = 0
    foreach ($r in $rows) {
        $n++
        $mark = if ($done.ContainsKey($r.id)) { "[" + $done[$r.id] + "]" } else { "[   ]" }
        "{0,2}. {1,-10} {2}  {3}" -f $n, $mark, $r.year, $r.title
    }
    exit 0
}

function Wrap-Text {
    param([string]$Text, [int]$Width = 98)
    if ([string]::IsNullOrWhiteSpace($Text)) { return @("(none)") }
    $out = New-Object System.Collections.Generic.List[string]
    $line = ""
    foreach ($w in ($Text -split '\s+')) {
        if ($line.Length -eq 0) { $line = $w }
        elseif (($line.Length + $w.Length + 1) -le $Width) { $line = $line + " " + $w }
        else { $out.Add($line); $line = $w }
    }
    if ($line.Length -gt 0) { $out.Add($line) }
    return $out
}

function Save-Verdict {
    param([string]$Id, [string]$Verdict, [string]$Note)
    $exists = Test-Path $Side
    if (-not $exists) { Set-Content -Path $Side -Value "id,verdict,note" -Encoding UTF8 }
    $clean = ($Note -replace '"', '""')
    Add-Content -Path $Side -Value ('{0},{1},"{2}"' -f $Id, $Verdict, $clean) -Encoding UTF8
}

$total = $rows.Count
$i = 0
foreach ($r in $rows) {
    $i++
    if ($Start -gt 0 -and $i -lt $Start) { continue }
    if ($done.ContainsKey($r.id)) { continue }

    Clear-Host
    $answered = $done.Count
    Write-Host ("=" * 100) -ForegroundColor DarkGray
    Write-Host (" Record {0} of {1}      answered so far: {2}      flagged: {3}" -f $i, $total, $answered, $r.flagged_because) -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host (" " + $r.title) -ForegroundColor White
    Write-Host (" {0}  |  {1}  |  {2}" -f $r.year, $r.db, ($(if ($r.doi) { "doi:" + $r.doi } else { "no DOI" }))) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host (" Model:  I1={0}  I2={1}  I3={2}  I4={3}   confidence {4}" -f $r.model_I1, $r.model_I2, $r.model_I3, $r.model_I4, $r.model_confidence)
    if ($r.model_reason) { Write-Host (" Reason: " + $r.model_reason) -ForegroundColor DarkGray }
    if ($r.I1_evidence_span) {
        Write-Host " I1 span quoted by the model:" -ForegroundColor DarkGray
        foreach ($l in Wrap-Text $r.I1_evidence_span) { Write-Host ("   " + $l) -ForegroundColor DarkYellow }
    } else {
        Write-Host " I1 span: (none quoted)" -ForegroundColor DarkYellow
    }
    Write-Host ""
    Write-Host " Abstract" -ForegroundColor Cyan
    Write-Host (" " + ("-" * 98)) -ForegroundColor DarkGray
    foreach ($l in Wrap-Text $r.abstract) { Write-Host (" " + $l) }
    Write-Host ""
    Write-Host " I1 group as an organised group | I2 crime or justice | I3 mechanism analysed | I4 empirical/documentary" -ForegroundColor DarkGray
    Write-Host ""

    while ($true) {
        $a = Read-Host " Your verdict  [I]nclude  [E]xclude  [S]kip  [Q]uit  [T]itle only"
        $a = ($a + "").Trim().ToLower()
        if ($a -eq "i") { $v = "INCLUDE"; break }
        if ($a -eq "e") { $v = "EXCLUDE"; break }
        if ($a -eq "s") { $v = ""; break }
        if ($a -eq "q") { Write-Host ""; Write-Host (" Stopped at record {0}. Progress saved." -f $i) -ForegroundColor Yellow; exit 0 }
        if ($a -eq "t") {
            Clear-Host
            Write-Host (" " + $r.title) -ForegroundColor White
            Write-Host (" " + $r.year + " | " + $r.db + " | " + $r.doi) -ForegroundColor DarkGray
            Write-Host ""
            if ($r.I1_evidence_span) { Write-Host (" I1 span: " + $r.I1_evidence_span) -ForegroundColor DarkYellow }
            Write-Host ""
            continue
        }
        Write-Host " Please type i, e, s, q or t." -ForegroundColor Red
    }

    if ($v -eq "") {
        Write-Host " Skipped." -ForegroundColor DarkGray
        Start-Sleep -Milliseconds 300
        continue
    }

    $note = Read-Host " One-line note (Enter to leave blank)"
    $note = ($note + "").Trim()
    Save-Verdict -Id $r.id -Verdict $v -Note $note
    $done[$r.id] = $v
    Write-Host (" Recorded: {0}." -f $v) -ForegroundColor Green
    Start-Sleep -Milliseconds 300
}

Clear-Host
$inc = ($done.Values | Where-Object { $_ -eq "INCLUDE" }).Count
$exc = ($done.Values | Where-Object { $_ -eq "EXCLUDE" }).Count
Write-Host ""
Write-Host (" Audited {0} of {1}.  INCLUDE {2}   EXCLUDE {3}" -f $done.Count, $total, $inc, $exc) -ForegroundColor Cyan
Write-Host ""
if ($done.Count -lt $total) {
    Write-Host (" {0} still blank. Re-run this script to continue." -f ($total - $done.Count)) -ForegroundColor Yellow
} else {
    Write-Host " All 30 answered. Next step, from the local/ folder:" -ForegroundColor Cyan
    Write-Host "   python src\apply_author_audit.py" -ForegroundColor White
}
Write-Host ""
