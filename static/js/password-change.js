function initPasswordChangePage() {  
    // 기존 이벤트 제거
    $(document).off('submit', '#passwordChangeForm');
    $(document).off('click', '#cancelBtn');
    $(document).off('focus blur input change', '.form-input');

    // 초기 비밀번호 요구사항 상태 설정
    updatePasswordRequirements('');

    // 폼 제출 처리
    $(document).on('submit', '#passwordChangeForm', function(e) {
        console.log('비밀번호 변경 폼 제출');
        e.preventDefault();
        e.stopPropagation();
        
        const formData = {
            userId: JSON.parse(localStorage.getItem('currentUser')).userId,
            currentPassword: $('#currentPassword').val(),
            newPassword: $('#newPassword').val(),
            confirmPassword: $('#confirmPassword').val()
        };
        
        // 유효성 검사
        if (!validatePasswordForm(formData)) {
            return;
        }
        
        // 로딩 상태
        const $button = $('#passwordChangeForm').find('.btn-primary');
        const originalText = $button.text();
        $button.text('변경 중...').prop('disabled', true);
        
        $.ajax({
            url: '/api/users/password',
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({
                userId: formData.userId,
                currentPassword: formData.currentPassword,
                newPassword: formData.newPassword
            }),
            success: function(response) {
                console.log('API 응답:', response);
                
                if (response.success) {
                    alert('비밀번호가 성공적으로 변경되었습니다.');
                    $('#passwordChangeForm')[0].reset();
                    $('.form-input').css('border-color', 'rgba(4, 7, 7, 0.2)');
                    updatePasswordRequirements('');
                } else {
                    alert(response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('비밀번호 변경 실패:', xhr.responseText);
                
                let errorMessage = '비밀번호 변경 중 오류가 발생했습니다.';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                
                alert(errorMessage);
            },
            complete: function() {
                // 로딩 상태 해제
                $button.text(originalText).prop('disabled', false);
            }
        });
    });

    // 취소 버튼
    $(document).on('click', '#cancelBtn', function(e) {
        e.preventDefault();
        if (confirm('입력한 내용이 모두 삭제됩니다. 계속하시겠습니까?')) {
            $('#passwordChangeForm')[0].reset();
            $('.form-input').css('border-color', 'rgba(4, 7, 7, 0.2)');
            updatePasswordRequirements('');
        }
    });

    // 입력 필드 포커스 효과
    $(document).on('focus', '.form-input', function() {
        $(this).parent().css('transform', 'scale(1.02)');
    }).on('blur', '.form-input', function() {
        $(this).parent().css('transform', 'scale(1)');
    });

    // 새 비밀번호 실시간 검증
    $(document).on('input', '#newPassword', function() {
        const password = $(this).val();
        updatePasswordRequirements(password);
        
        // 확인 비밀번호와 비교
        const confirmPassword = $('#confirmPassword').val();
        if (confirmPassword) {
            validatePasswordMatch(password, confirmPassword);
        }
    });

    // 비밀번호 확인 실시간 검증
    $(document).on('input', '#confirmPassword', function() {
        const newPassword = $('#newPassword').val();
        const confirmPassword = $(this).val();
        validatePasswordMatch(newPassword, confirmPassword);
    });

    // 입력 필드 실시간 유효성 검사
    $(document).on('input change', '.form-input', function() {
        const $input = $(this);
        if ($input.val().trim()) {
            $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    });

    // 폼 유효성 검사
    function validatePasswordForm(formData) {
        let isValid = true;
        
        // 필수 필드 확인
        const $inputs = $('#passwordChangeForm').find('.form-input');
        $inputs.each(function() {
            const $input = $(this);
            if (!$input.val().trim()) {
                $input.css('border-color', '#ED1C24');
                isValid = false;
            } else {
                $input.css('border-color', 'rgba(4, 7, 7, 0.2)');
            }
        });

        if (!isValid) {
            alert('모든 필드를 입력해주세요.');
            return false;
        }

        // 새 비밀번호 요구사항 확인
        if (!isPasswordValid(formData.newPassword)) {
            alert('새 비밀번호가 요구사항을 만족하지 않습니다.');
            $('#newPassword').css('border-color', '#ED1C24');
            return false;
        }

        // 비밀번호 확인
        if (formData.newPassword !== formData.confirmPassword) {
            alert('새 비밀번호와 확인 비밀번호가 일치하지 않습니다.');
            $('#confirmPassword').css('border-color', '#ED1C24');
            return false;
        }

        // 현재 비밀번호와 새 비밀번호 동일성 확인
        if (formData.currentPassword === formData.newPassword) {
            alert('새 비밀번호는 현재 비밀번호와 달라야 합니다.');
            $('#newPassword').css('border-color', '#ED1C24');
            return false;
        }

        return true;
    }

    // 비밀번호 요구사항 확인
    function isPasswordValid(password) {
        const requirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };
        
        return Object.values(requirements).every(req => req);
    }

    // 비밀번호 요구사항 UI 업데이트
    function updatePasswordRequirements(password) {
        const requirements = [
            { test: password.length >= 8, text: '8자 이상' },
            { test: /[A-Z]/.test(password), text: '대문자 포함' },
            { test: /[a-z]/.test(password), text: '소문자 포함' },
            { test: /\d/.test(password), text: '숫자 포함' },
            { test: /[!@#$%^&*(),.?":{}|<>]/.test(password), text: '특수문자 포함' }
        ];

        $('.requirement-item').each(function(index) {
            const $item = $(this);
            const $icon = $item.find('.requirement-icon');
            const requirement = requirements[index];
            
            if (requirement && requirement.test) {
                $icon.css('background-color', '#28a745').text('✓');
            } else {
                $icon.css('background-color', '#dc3545').text('X');
            }
        });
    }

    // 비밀번호 일치 확인
    function validatePasswordMatch(newPassword, confirmPassword) {
        const $confirmInput = $('#confirmPassword');
        
        if (confirmPassword && newPassword !== confirmPassword) {
            $confirmInput.css('border-color', '#ED1C24');
        } else {
            $confirmInput.css('border-color', 'rgba(4, 7, 7, 0.2)');
        }
    }
}