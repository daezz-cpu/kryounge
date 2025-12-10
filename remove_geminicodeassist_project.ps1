# Cursor 설정에서 geminicodeassist.project 항목 삭제 스크립트
# 사용 방법: Cursor를 완전히 종료한 후 이 스크립트를 실행하세요

$settingsFile = "$env:APPDATA\Cursor\User\settings.json"

Write-Host "설정 파일 확인 중..." -ForegroundColor Yellow

if (-not (Test-Path $settingsFile)) {
    Write-Host "설정 파일을 찾을 수 없습니다: $settingsFile" -ForegroundColor Red
    exit 1
}

# Cursor 프로세스 확인
$cursorProcesses = Get-Process | Where-Object {$_.ProcessName -like "*cursor*"}
if ($cursorProcesses) {
    Write-Host "`n경고: Cursor가 실행 중입니다!" -ForegroundColor Red
    Write-Host "다음 프로세스가 실행 중입니다:" -ForegroundColor Yellow
    $cursorProcesses | ForEach-Object { Write-Host "  - $($_.ProcessName) (PID: $($_.Id))" }
    Write-Host "`nCursor를 완전히 종료한 후 다시 시도하세요." -ForegroundColor Yellow
    Write-Host "계속하시겠습니까? (Y/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne "Y" -and $response -ne "y") {
        Write-Host "취소되었습니다." -ForegroundColor Yellow
        exit 0
    }
}

try {
    Write-Host "`n설정 파일 읽는 중..." -ForegroundColor Yellow
    $content = Get-Content $settingsFile -Raw -Encoding UTF8
    $json = $content | ConvertFrom-Json
    
    if ($json.PSObject.Properties.Name -contains 'geminicodeassist.project') {
        Write-Host "geminicodeassist.project 항목을 찾았습니다: $($json.'geminicodeassist.project')" -ForegroundColor Yellow
        
        # 항목 삭제
        $json.PSObject.Properties.Remove('geminicodeassist.project')
        
        # JSON 변환 및 저장
        $newContent = $json | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($settingsFile, $newContent, [System.Text.Encoding]::UTF8)
        
        Write-Host "`n성공적으로 삭제되었습니다!" -ForegroundColor Green
        Write-Host "이제 Cursor를 다시 시작하세요." -ForegroundColor Green
    } else {
        Write-Host "`ngeminicodeassist.project 항목이 설정 파일에 없습니다." -ForegroundColor Green
    }
    
    # 확인
    Start-Sleep -Milliseconds 500
    $verify = Get-Content $settingsFile -Raw | ConvertFrom-Json
    if ($verify.PSObject.Properties.Name -contains 'geminicodeassist.project') {
        Write-Host "`n경고: 항목이 여전히 존재합니다. Cursor가 자동으로 복원했을 수 있습니다." -ForegroundColor Red
    } else {
        Write-Host "`n확인 완료: 항목이 성공적으로 삭제되었습니다." -ForegroundColor Green
    }
    
} catch {
    Write-Host "`n오류 발생: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}


