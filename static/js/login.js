$(document).ready(function() {
    // 로그인 폼 제출 처리
    $('#loginForm').on('submit', function(e) {
        e.preventDefault();
        
        $.ajax({
            url: '/api/test',
            method: 'GET',
            success: function(response) {
                console.log('✓ DB 연결 성공:', response);
                console.log('ACCESS 테이블 데이터:', response.data);
            },
            error: function(xhr, status, error) {
                console.error('✗ DB 연결 실패:', error);
                console.error('에러 상세:', xhr.responseText);
            }
        });

        // const $inputs = $(this).find('.form-input');
        // let isValid = true;
        
        // // 간단한 유효성 검사
        // $inputs.each(function() {
        //     const $input = $(this);
        //     if (!$input.val().trim()) {
        //         $input.css('border-color', '#ED1C24');
        //         isValid = false;
        //     } else {
        //         $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
        //     }
        // });
        
        // if (isValid) {
        //     // 로그인 버튼 로딩 상태
        //     // const $button = $(this).find('.login-button');
        //     // const originalText = $button.text();
        //     // $button.text('로그인 중...').prop('disabled', true);

            
            
        //     // // TODO: 실제 로그인 API 호출
        //     // setTimeout(function() {
        //     //     alert('로그인 성공! (데모)');
        //     //     $button.text(originalText).prop('disabled', false);
                
        //     //     window.location.href = 'landing';
        //     // }, 2000);
        // } else {
        //     alert('모든 필드를 입력해주세요.');
        // }
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
    
    // 입력 필드 실시간 유효성 검사 (에러 상태 해제)
    $('.form-input').on('input', function() {
        const $input = $(this);
        if ($input.val().trim()) {
            $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    });
    
    // 로그인 시도 횟수 제한 (보안 강화)
    let loginAttempts = 0;
    const maxAttempts = 5;
    
    function checkLoginAttempts() {
        if (loginAttempts >= maxAttempts) {
            $('#loginForm input, #loginForm button').prop('disabled', true);
            alert('로그인 시도 횟수가 초과되었습니다. 잠시 후 다시 시도해주세요.');
            
            // 5분 후 다시 활성화
            setTimeout(function() {
                $('#loginForm input, #loginForm button').prop('disabled', false);
                loginAttempts = 0;
            }, 300000); // 5분
            
            return false;
        }
        return true;
    }
    
    // 폼 제출 시 시도 횟수 체크 추가
    $('#loginForm').on('submit', function(e) {
        if (!checkLoginAttempts()) {
            e.preventDefault();
            return;
        }
        loginAttempts++;
    });
    
    // 개발자 도구에서 쉽게 테스트할 수 있도록 함수 노출
    window.resetLoginAttempts = function() {
        loginAttempts = 0;
        $('#loginForm input, #loginForm button').prop('disabled', false);
        console.log('로그인 시도 횟수가 초기화되었습니다.');
    };
});