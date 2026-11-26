<#
  逐条判读 30 条被标记的记录（中文界面）。

  用法（在 local 目录下）：
      powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_read_zh.ps1
      powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_read_zh.ps1 -Start 12
      powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_read_zh.ps1 -Index

  每判一条立刻保存；关掉窗口不会丢，重跑即从下一条继续。
  判定写入 out\supplements\S10_verdicts.csv（独立小文件），
  工作表本身不会被改写，摘要不会因编码往返受损。

  屏幕上的标题和摘要是英文原文，不做翻译：判读的对象就是原文。
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

if (-not (Test-Path $Form)) { Write-Host "找不到工作表：$Form" -ForegroundColor Red; exit 1 }

$rows = Import-Csv -Path $Form -Encoding UTF8

$done = @{}
if (Test-Path $Side) {
    Import-Csv -Path $Side -Encoding UTF8 | ForEach-Object {
        if ($_.id) { $done[$_.id] = $_.verdict }
    }
}

$reasonZh = @{
    "metaphor"       = "全文只有比喻用法"
    "no group named" = "标题与模型自引证据都未点名群体"
    "both"           = "两项都命中"
}

if ($Index) {
    $n = 0
    foreach ($r in $rows) {
        $n++
        $mark = if ($done.ContainsKey($r.id)) { "[" + $done[$r.id] + "]" } else { "[      ]" }
        "{0,2}. {1,-10} {2}  {3}" -f $n, $mark, $r.year, $r.title
    }
    exit 0
}

function Wrap-Text {
    param([string]$Text, [int]$Width = 96)
    if ([string]::IsNullOrWhiteSpace($Text)) { return @("（无）") }
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
    if (-not (Test-Path $Side)) { Set-Content -Path $Side -Value "id,verdict,note" -Encoding UTF8 }
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
    $flag = $reasonZh[$r.flagged_because]
    if (-not $flag) { $flag = $r.flagged_because }

    Write-Host ("=" * 100) -ForegroundColor DarkGray
    Write-Host (" 第 {0} 条 / 共 {1} 条      已判 {2} 条      标记原因：{3}" -f $i, $total, $done.Count, $flag) -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host (" " + $r.title) -ForegroundColor White
    $src = if ($r.doi) { "doi:" + $r.doi } else { "无 DOI" }
    Write-Host (" {0}  |  {1}  |  {2}" -f $r.year, $r.db, $src) -ForegroundColor DarkGray
    Write-Host ""

    $y = { param($v) if ($v -eq "True") { "是" } else { "否" } }
    Write-Host (" 模型判定：I1={0}  I2={1}  I3={2}  I4={3}    置信度 {4}" -f (& $y $r.model_I1), (& $y $r.model_I2), (& $y $r.model_I3), (& $y $r.model_I4), $r.model_confidence)
    if ($r.model_reason) { Write-Host (" 模型理由：" + $r.model_reason) -ForegroundColor DarkGray }

    Write-Host ""
    if ($r.I1_evidence_span) {
        Write-Host " 模型为 I1 引用的原文：" -ForegroundColor DarkGray
        foreach ($l in Wrap-Text $r.I1_evidence_span) { Write-Host ("   " + $l) -ForegroundColor DarkYellow }
    } else {
        Write-Host " 模型未引用任何 I1 证据。" -ForegroundColor DarkYellow
    }

    Write-Host ""
    Write-Host " 摘要（原文）" -ForegroundColor Cyan
    Write-Host (" " + ("-" * 98)) -ForegroundColor DarkGray
    foreach ($l in Wrap-Text $r.abstract) { Write-Host (" " + $l) }
    Write-Host ""
    Write-Host " 判据：I1 是真实存在的组织性群体 · I2 犯罪或刑事司法 · I3 分析而非仅提及机制 · I4 有经验或文献材料" -ForegroundColor DarkGray
    Write-Host ""

    while ($true) {
        $a = Read-Host " 请选择  [I] 纳入  [E] 排除  [S] 跳过  [Q] 退出  [T] 只看标题"
        $a = ($a + "").Trim().ToLower()
        if ($a -eq "i") { $v = "INCLUDE"; break }
        if ($a -eq "e") { $v = "EXCLUDE"; break }
        if ($a -eq "s") { $v = ""; break }
        if ($a -eq "q") {
            Write-Host ""
            Write-Host (" 已在第 {0} 条停止，进度已保存。" -f $i) -ForegroundColor Yellow
            exit 0
        }
        if ($a -eq "t") {
            Clear-Host
            Write-Host (" " + $r.title) -ForegroundColor White
            Write-Host (" {0} | {1} | {2}" -f $r.year, $r.db, $src) -ForegroundColor DarkGray
            Write-Host ""
            if ($r.I1_evidence_span) { Write-Host (" I1 证据：" + $r.I1_evidence_span) -ForegroundColor DarkYellow }
            Write-Host ""
            continue
        }
        Write-Host " 请输入 i、e、s、q 或 t。" -ForegroundColor Red
    }

    if ($v -eq "") {
        Write-Host " 已跳过。" -ForegroundColor DarkGray
        Start-Sleep -Milliseconds 300
        continue
    }

    $note = Read-Host " 一行备注（直接回车留空）"
    $note = ($note + "").Trim()
    Save-Verdict -Id $r.id -Verdict $v -Note $note
    $done[$r.id] = $v
    $label = if ($v -eq "INCLUDE") { "纳入" } else { "排除" }
    Write-Host (" 已记录：{0}。" -f $label) -ForegroundColor Green
    Start-Sleep -Milliseconds 300
}

Clear-Host
$inc = ($done.Values | Where-Object { $_ -eq "INCLUDE" }).Count
$exc = ($done.Values | Where-Object { $_ -eq "EXCLUDE" }).Count
Write-Host ""
Write-Host (" 已判 {0} / {1} 条。纳入 {2} 条，排除 {3} 条。" -f $done.Count, $total, $inc, $exc) -ForegroundColor Cyan
Write-Host ""
if ($done.Count -lt $total) {
    Write-Host (" 还有 {0} 条未判，重跑本脚本即可继续。" -f ($total - $done.Count)) -ForegroundColor Yellow
} else {
    Write-Host " 30 条已全部判完。回到 local 目录执行：" -ForegroundColor Cyan
    Write-Host "   python src\apply_author_audit.py" -ForegroundColor White
}
Write-Host ""
