$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$treeBuild = $PSScriptRoot
Add-Type -Path (Join-Path $treeBuild 'capture.cs') -ReferencedAssemblies @([System.Speech.Synthesis.SpeechSynthesizer].Assembly.Location, 'System.ComponentModel.Primitives', 'System.Runtime', 'System.Collections')
$treeScenes = Get-Content -Raw -LiteralPath (Join-Path $treeBuild 'scenes.json') | ConvertFrom-Json
$treeAudio = Join-Path $treeBuild 'audio-local'
New-Item -ItemType Directory -Force -Path $treeAudio | Out-Null
$treeSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$treeSynth.SelectVoice('Microsoft Zira Desktop')
$treeSynth.Rate = 0
$treeSynth.Volume = 100
for ($treeIndex=0; $treeIndex -lt $treeScenes.Count; $treeIndex++) {
    $treeName = '{0:D2}' -f ($treeIndex+1)
    $treeOut = Join-Path $treeAudio ($treeName + '.wav')
    $treeJson = Join-Path $treeAudio ($treeName + '.json')
    $treeMarks = [TreeSpeechCapture]::Speak($treeSynth, $treeScenes[$treeIndex].narration, $treeOut)
    $treeMarks | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $treeJson -Encoding utf8
    Write-Output ('Voiced ' + $treeName + '/' + $treeScenes.Count)
}
$treeSynth.Dispose()
