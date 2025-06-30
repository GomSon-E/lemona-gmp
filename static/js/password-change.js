function initPasswordChangePage() {
    console.log('비밀번호 변경 페이지 초기화');
    
    // 기존 이벤트 제거
    $(document).off('submit', '#passwordChangeForm');
    $(document).off('click', '#cancelBtn');
    $(document).off('focus blur input change', '.form-input');

    // 폼 제출 처리
    $(document).on('submit', '#passwordChangeForm', function(e) {
        console.log('비밀번호 변경 폼 제출');
        e.preventDefault();
        e.stopPropagation();
        
        // 임시 알림
        alert('비밀번호 변경 기능은 준비 중입니다.');
    });

    // 취소 버튼
    $(document).on('click', '#cancelBtn', function(e) {
        e.preventDefault();
        if (confirm('입력한 내용이 모두 삭제됩니다. 계속하시겠습니까?')) {
            $('#passwordChangeForm')[0].reset();
            $('.form-input').css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    });

    // 입력 필드 포커스 효과
    $(document).on('focus', '.form-input', function() {
        $(this).parent().css('transform', 'scale(1.02)');
    }).on('blur', '.form-input', function() {
        $(this).parent().css('transform', 'scale(1)');
    });

    // 입력 필드 실시간 유효성 검사
    $(document).on('input change', '.form-input', function() {
        const $input = $(this);
        if ($input.val().trim()) {
            $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    });
}