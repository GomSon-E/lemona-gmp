function initPlcTestPage() {
    // 기존 이벤트 제거
    $(document).off('click', '#readDataBtn, #checkStatusBtn');

    // 데이터 읽기 버튼 이벤트
    $(document).on('click', '#readDataBtn', function() {
        readPlcData();
    });

    // 연결 상태 확인 버튼 이벤트
    $(document).on('click', '#checkStatusBtn', function() {
        checkPlcStatus();
    });

    // PLC 데이터 읽기
    function readPlcData() {
        const $button = $('#readDataBtn');
        const originalText = $button.text();
        
        // 로딩 상태
        $button.html('<span class="loading-spinner"></span>읽는 중...').prop('disabled', true);
        
        $.ajax({
            url: '/api/plc/read',
            method: 'GET',
            success: function(response) {
                displayResult(response, 'PLC 데이터 읽기 결과');
            },
            error: function(xhr, status, error) {
                console.error('PLC 데이터 읽기 실패:', error);
                
                let errorMessage = 'PLC 통신 중 오류가 발생했습니다.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                
                displayResult({
                    success: false,
                    message: errorMessage
                }, 'PLC 데이터 읽기 결과');
            },
            complete: function() {
                $button.text(originalText).prop('disabled', false);
            }
        });
    }

    // PLC 연결 상태 확인
    function checkPlcStatus() {
        const $button = $('#checkStatusBtn');
        const originalText = $button.text();
        
        // 로딩 상태
        $button.html('<span class="loading-spinner"></span>확인 중...').prop('disabled', true);
        
        $.ajax({
            url: '/api/plc/status',
            method: 'GET',
            success: function(response) {
                displayResult(response, 'PLC 연결 상태 확인 결과');
            },
            error: function(xhr, status, error) {
                console.error('PLC 상태 확인 실패:', error);
                
                let errorMessage = 'PLC 상태 확인 중 오류가 발생했습니다.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                
                displayResult({
                    success: false,
                    message: errorMessage
                }, 'PLC 연결 상태 확인 결과');
            },
            complete: function() {
                $button.text(originalText).prop('disabled', false);
            }
        });
    }

    // 결과 표시
    function displayResult(response, title) {
        const $container = $('#resultContainer');
        
        let resultHtml = `<h4>${title}</h4>`;
        
        if (response.success) {
            resultHtml += `<div class="result-success">✅ ${response.message}</div>`;
            
            if (response.data) {
                resultHtml += `
                    <div class="result-data">
                        <pre>${JSON.stringify(response.data, null, 2)}</pre>
                    </div>
                `;
            }
        } else {
            resultHtml += `<div class="result-error">❌ ${response.message}</div>`;
        }
        
        $container.html(resultHtml);
        
        // 결과 섹션으로 스크롤
        $container[0].scrollIntoView({ behavior: 'smooth' });
    }
}