function initBackupRestorePage() {
    // 기존 이벤트 제거
    $(document).off('click', '#createBackupBtn, #restoreDataBtn, #removeFileBtn');
    $(document).off('change', '#backupFileInput');

    // 전역 변수
    window.selectedBackupFile = null;

    // 백업 생성 버튼
    $(document).on('click', '#createBackupBtn', function() {
        createBackup();
    });

    // 파일 선택 관련 이벤트
    $(document).on('click', '#uploadArea', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#backupFileInput').trigger('click');
    });

    $(document).on('change', '#backupFileInput', function(e) {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // 파일 제거 버튼
    $(document).on('click', '#removeFileBtn', function() {
        removeSelectedFile();
    });

    // 데이터 복원 버튼
    $(document).on('click', '#restoreDataBtn', function() {
        restoreData();
    });

    // 백업 생성
    function createBackup() {
        const $button = $('#createBackupBtn');
        const originalText = $button.text();
        
        $button.addClass('loading').prop('disabled', true);
        
        $.ajax({
            url: '/api/backup/create',
            method: 'POST',
            success: function(response) {
                displayBackupResult(response, '백업 생성 결과');
            },
            error: function(xhr, status, error) {
                console.error('백업 생성 실패:', error);
                
                let errorMessage = '백업 생성 중 오류가 발생했습니다.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                
                displayBackupResult({
                    success: false,
                    message: errorMessage
                }, '백업 생성 결과');
            },
            complete: function() {
                $button.removeClass('loading').prop('disabled', false);
            }
        });
    }

    // 파일 선택 처리
    function handleFileSelect(file) {
        if (!file) {
            return;
        }
        
        console.log('선택된 파일:', file.name, file.size);
        
        // 파일 확장자 검사
        if (!file.name.toLowerCase().endsWith('.bak')) {
            alert('BAK 파일만 선택할 수 있습니다.');
            return;
        }
        
        window.selectedBackupFile = file;
        
        // UI 업데이트
        $('#fileName').text(file.name);
        $('#fileSize').text(formatFileSize(file.size));
        $('#uploadArea').hide();
        $('#selectedFile').show();
        
        // 버튼 활성화
        $('#restoreDataBtn').prop('disabled', false);
        
        // 결과 메시지 초기화
        $('#restoreResult').html('<div class="no-result-message">파일이 선택되었습니다. 복원 버튼을 클릭하여 진행하세요.</div>');
        
        console.log('파일 선택 완료');
    }

    // 선택된 파일 제거
    function removeSelectedFile() {
        window.selectedBackupFile = null;
        $('#selectedFile').hide();
        $('#uploadArea').show();
        $('#restoreDataBtn').prop('disabled', true);
        $('#restoreResult').html('<div class="no-result-message">BAK 파일을 선택하여 데이터를 복원하세요.</div>');
        $('#backupFileInput').val('');
    }

    // 데이터 복원
    function restoreData() {
        if (!window.selectedBackupFile) {
            alert('파일을 먼저 선택해주세요.');
            return;
        }
        
        const confirmMessage = `데이터 복원을 진행하시겠습니까?\n\n⚠️ 경고:\n- 현재 데이터베이스가 백업 파일의 데이터로 복원됩니다.\n- 이 작업은 되돌릴 수 없습니다.\n- 복원 중에는 시스템 사용이 제한됩니다.\n\n파일명: ${window.selectedBackupFile.name}`;
        
        if (!confirm(confirmMessage)) {
            return;
        }
        
        // 최종 확인
        if (!confirm('정말로 데이터 복원을 실행하시겠습니까?')) {
            return;
        }
        
        const $button = $('#restoreDataBtn');
        $button.addClass('loading').prop('disabled', true);
        
        const formData = new FormData();
        formData.append('backup_file', window.selectedBackupFile);
        
        $.ajax({
            url: '/api/backup/restore',
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            timeout: 300000, // 5분 타임아웃
            success: function(response) {
                displayRestoreResult(response, '데이터 복원 결과');
                if (response.success) {
                    setTimeout(() => {
                        if (confirm('데이터 복원이 완료되었습니다. 시스템을 다시 시작하시겠습니까?')) {
                            window.location.href = '/login';
                        }
                    }, 2000);
                }
            },
            error: function(xhr, status, error) {
                console.error('데이터 복원 실패:', error);
                
                let errorMessage = '데이터 복원 중 오류가 발생했습니다.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                
                displayRestoreResult({
                    success: false,
                    message: errorMessage
                }, '데이터 복원 결과');
            },
            complete: function() {
                $button.removeClass('loading').prop('disabled', false);
            }
        });
    }

    // 백업 결과 표시
    function displayBackupResult(response, title) {
        const $container = $('#backupResult');
        
        let resultHtml = `<h4 style="margin-bottom: 15px;">${title}</h4>`;
        
        if (response.success) {
            resultHtml += `<div class="result-success">✅ ${response.message}</div>`;
            
            if (response.data) {
                resultHtml += `
                    <div class="result-data">
                        ${JSON.stringify(response.data, null, 2)}
                    </div>
                `;
            }
        } else {
            resultHtml += `<div class="result-error">❌ ${response.message}</div>`;
        }
        
        $container.html(resultHtml);
        $container[0].scrollIntoView({ behavior: 'smooth' });
    }

    // 복원 결과 표시
    function displayRestoreResult(response, title) {
        const $container = $('#restoreResult');
        
        let resultHtml = `<h4 style="margin-bottom: 15px;">${title}</h4>`;
        
        if (response.success) {
            resultHtml += `<div class="result-success">✅ ${response.message}</div>`;
            
            if (response.data) {
                resultHtml += `
                    <div class="result-info">
                        <strong>복원 정보:</strong><br>
                        ${Object.entries(response.data).map(([key, value]) => `${key}: ${value}`).join('<br>')}
                    </div>
                `;
            }
        } else {
            resultHtml += `<div class="result-error">❌ ${response.message}</div>`;
        }
        
        $container.html(resultHtml);
        $container[0].scrollIntoView({ behavior: 'smooth' });
    }

    // 파일 크기 포맷팅
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}