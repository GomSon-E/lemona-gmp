$(document).ready(function() {
    // 로그인 폼 제출 처리
    $('#loginForm').on('submit', function(e) {
        e.preventDefault();

        const $inputs = $(this).find('.form-input');
        let isValid = true;
        
        // 간단한 유효성 검사
        $inputs.each(function() {
            const $input = $(this);
            if (!$input.val().trim()) {
                $input.css('border-color', '#ED1C24');
                isValid = false;
            } else {
                $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
            }
        });
        
        if (isValid) {
            // 로그인 버튼 로딩 상태
            const $button = $(this).find('.login-button');
            const originalText = $button.text();
            $button.text('로그인 중...').prop('disabled', true);

            // TODO: 실제 로그인 API 호출
            setTimeout(function() {
                alert('로그인 성공! (데모)');
                $button.text(originalText).prop('disabled', false);
                
                window.location.href = 'landing';
            }, 2000);
        } else {
            alert('모든 필드를 입력해주세요.');
        }
    });
    
    // Enter 키로 로그인
    $(document).on('keypress', function(e) {
        if (e.which === 13) { // Enter 키
            $('#loginForm').trigger('submit');
        }
    });
    
    // 입력 필드 포커스 효과
    $('.form-input').on('focus', function() {
        $(this).parent().css('transform', 'scale(1.02)');
    }).on('blur', function() {
        $(this).parent().css('transform', 'scale(1)');
    });
    
    // 입력 필드 실시간 유효성 검사
    $('.form-input').on('input', function() {
        const $input = $(this);
        if ($input.val().trim()) {
            $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    });
});