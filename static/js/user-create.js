function initUserCreatePage() {
    console.log('사용자 생성 페이지 초기화 시작');
    
    $(document).off('submit', '#userCreateForm');
    $(document).off('click', '#cancelBtn');
    $(document).off('focus blur input change', '.form-input, .form-select');

    $(document).on('submit', '#userCreateForm', function(e) {
        console.log('폼 제출 이벤트 발생');
        e.preventDefault();
        e.stopPropagation();
        
        const formData = {
            userId: $('#userId').val(),
            fullName: $('#fullName').val(),
            division: $('#division').val(),
            role: $('#userRole').val()
        };
        
        console.log('폼 데이터:', formData);
        
        // 간단한 유효성 검사
        let isValid = true;
        const $inputs = $('#userCreateForm').find('.form-input, .form-select');
        
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
            // 로딩 상태
            const $button = $('#userCreateForm').find('.btn-primary');
            const originalText = $button.text();
            $button.text('생성 중...').prop('disabled', true);
            
            // TODO: 실제 사용자 생성 API 호출
            setTimeout(function() {
                alert('사용자가 성공적으로 생성되었습니다!\n\n' + 
                        'ID: ' + formData.userId + '\n' +
                        '이름: ' + formData.fullName + '\n' +
                        '부서: ' + formData.division + '\n' +
                        '권한: ' + formData.role);
                
                // 폼 초기화
                $('#userCreateForm')[0].reset();
                $button.text(originalText).prop('disabled', false);
                
                // 입력 필드 스타일 초기화
                $('.form-input, .form-select').css('border-color', 'rgba(4, 7, 7, 0.2)');
            }, 2000);
        } else {
            alert('모든 필드를 입력해주세요.');
        }
    });

    // 취소 버튼 - document에 이벤트 위임
    $(document).on('click', '#cancelBtn', function(e) {
        e.preventDefault();
        if (confirm('입력한 내용이 모두 삭제됩니다. 계속하시겠습니까?')) {
            $('#userCreateForm')[0].reset();
            $('.form-input, .form-select').css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    });

    // 입력 필드 포커스 효과 - document에 이벤트 위임
    $(document).on('focus', '.form-input, .form-select', function() {
        $(this).parent().css('transform', 'scale(1.02)');
    }).on('blur', '.form-input, .form-select', function() {
        $(this).parent().css('transform', 'scale(1)');
    });

    // 입력 필드 실시간 유효성 검사 - document에 이벤트 위임
    $(document).on('input change', '.form-input, .form-select', function() {
        const $input = $(this);
        if ($input.val().trim()) {
            $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    });

    console.log('사용자 생성 페이지가 초기화되었습니다.');
    
    // 폼이 존재하는지 확인
    if ($('#userCreateForm').length > 0) {
        console.log('폼 요소를 찾았습니다:', $('#userCreateForm'));
    } else {
        console.error('폼 요소를 찾을 수 없습니다!');
    }
}