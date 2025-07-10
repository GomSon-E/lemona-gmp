function initUserCreatePage() {    
    $(document).off('submit', '#userCreateForm');
    $(document).off('click', '#cancelBtn');
    $(document).off('focus blur input change', '.form-input, .form-select');

    setupRoleOptions();

    $(document).on('submit', '#userCreateForm', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const currentUser = JSON.parse(localStorage.getItem('currentUser'));
        
        const formData = {
            userId: $('#userId').val(),
            fullName: $('#fullName').val(),
            division: $('#division').val(),
            role: $('#userRole').val(),
            currentUserId: currentUser.userId,
            loginHistoryId: currentUser.loginHistoryId 
        };
        
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
            
            $.ajax({
                url: '/api/users',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(formData),
                success: function(response) {
                    console.log('API 응답:', response);
                    
                    if (response.success) {
                        alert(`사용자가 성공적으로 생성되었습니다!\n\nID: ${response.data.userId}\n\n임시 비밀번호: ${response.data.defaultPassword}`);
                        $('#userCreateForm')[0].reset();
                        $('.form-input, .form-select').css('border-color', 'rgba(4, 7, 7, 0.2)');
                        setupRoleOptions();
                    } else {
                        alert(response.message);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('사용자 생성 실패:', xhr.responseText);
                    
                    let errorMessage = '사용자 생성 중 오류가 발생했습니다.';
                    
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
            setupRoleOptions();
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

    // ! 사용자 권한에 따른 역할 옵션 설정
    function setupRoleOptions() {
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
        const currentUserRole = currentUser.roleId;
        const $roleSelect = $('#userRole');
        
        // 기존 옵션 제거 (기본 옵션 제외)
        $roleSelect.find('option:not(:first)').remove();
        
        // 권한별 생성 가능한 역할 정의
        let availableRoles = [];
        
        if (currentUserRole === 1) { // ROOT
            availableRoles = [
                { value: '2', text: 'ADMIN (관리자)' }
            ];
        } else if (currentUserRole === 2) { // ADMIN
            availableRoles = [
                { value: '3', text: 'MANAGER (매니저)' },
                { value: '4', text: 'USER (사용자)' }
            ];
        }
        
        // 옵션 추가
        availableRoles.forEach(role => {
            $roleSelect.append(`<option value="${role.value}">${role.text}</option>`);
        });
    }
}