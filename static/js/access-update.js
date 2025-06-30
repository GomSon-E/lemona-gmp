function initAccessUpdatePage() {
    // 기존 이벤트 제거
    $(document).off('change', '#roleSelect');
    $(document).off('click', '.add-btn, .remove-btn');
    $(document).off('click', '#saveBtn, #resetBtn');

    // 전역 변수
    window.allPages = [];
    window.currentAccess = [];
    window.originalAccess = [];
    window.selectedRoleId = null;

    // 초기 데이터 로드
    loadRoles();
    loadAllPages();

    // 권한 선택 이벤트
    $(document).on('change', '#roleSelect', function() {
        const roleId = $(this).val();
        window.selectedRoleId = roleId;
        
        if (roleId) {
            loadRoleAccess(roleId);
            $('#saveBtn, #resetBtn').prop('disabled', false);
        } else {
            // 권한 선택 해제시 초기 상태로
            $('#currentPages, #availablePages').html('<div class="empty-message">권한을 선택해주세요.</div>');
            $('#saveBtn, #resetBtn').prop('disabled', true);
            window.currentAccess = [];
            window.originalAccess = [];
        }
    });

    // 페이지 추가/제거 버튼 이벤트
    $(document).on('click', '.add-btn', function() {
        const pageId = $(this).data('page-id');
        addPageToRole(pageId);
    });

    $(document).on('click', '.remove-btn', function() {
        const pageId = $(this).data('page-id');
        removePageFromRole(pageId);
    });

    // 저장 버튼
    $(document).on('click', '#saveBtn', function() {
        saveAccessChanges();
    });

    // 초기화 버튼
    $(document).on('click', '#resetBtn', function() {
        resetChanges();
    });

    // 권한 목록 로드 (ADMIN만 가능)
    function loadRoles() {
        const currentUser = JSON.parse(localStorage.getItem('currentUser'));
        const currentUserRole = currentUser.roleId;
        const $roleSelect = $('#roleSelect');
        
        // ADMIN이 아니면 접근 불가
        if (currentUserRole !== 2) {
            alert('권한이 없습니다.');
            return;
        }
        
        // 기존 옵션 제거
        $roleSelect.find('option:not(:first)').remove();
        
        // ADMIN이 관리할 수 있는 권한들
        const availableRoles = [
            { id: 3, name: 'MANAGER (매니저)' },
            { id: 4, name: 'USER (사용자)' }
        ];
        
        // 옵션 추가
        availableRoles.forEach(role => {
            $roleSelect.append(`<option value="${role.id}">${role.name}</option>`);
        });
    }

    // 전체 페이지 목록 로드
    function loadAllPages() {
        $.ajax({
            url: '/api/pages',
            method: 'GET',
            success: function(response) {
                if (response.success) {
                    window.allPages = response.data;
                } else {
                    console.error('페이지 목록 로드 실패:', response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('페이지 목록 로드 오류:', error);
            }
        });
    }

    // 특정 권한의 접근 권한 로드
    function loadRoleAccess(roleId) {
        $('#currentPages, #availablePages').html('<div class="loading">로딩 중입니다...</div>');
        
        $.ajax({
            url: `/api/access/${roleId}`,
            method: 'GET',
            success: function(response) {
                if (response.success) {
                    window.currentAccess = response.data.pages || [];
                    window.originalAccess = [...window.currentAccess];
                    updateAccessDisplay();
                } else {
                    showError('접근 권한 정보를 불러올 수 없습니다.');
                }
            },
            error: function(xhr, status, error) {
                console.error('접근 권한 조회 오류:', error);
                showError('접근 권한 조회 중 오류가 발생했습니다.');
            }
        });
    }

    // 접근 권한 화면 업데이트
    function updateAccessDisplay() {
        updateCurrentPages();
        updateAvailablePages();
    }

    // 현재 접근 가능한 페이지 표시
    function updateCurrentPages() {
        const $container = $('#currentPages');
        
        if (window.currentAccess.length === 0) {
            $container.html('<div class="empty-message">접근 가능한 페이지가 없습니다.</div>');
            return;
        }

        const html = window.currentAccess.map(page => `
            <div class="page-item current">
                <div class="page-info">
                    <div class="page-name">${page.PAGE_NAME}</div>
                    <div class="page-menu">${page.MENU_NAME}</div>
                </div>
                <button class="page-action remove-btn" data-page-id="${page.PAGE_ID}">제거</button>
            </div>
        `).join('');
        
        $container.html(html);
    }

    // 추가 가능한 페이지 표시
    function updateAvailablePages() {
        const $container = $('#availablePages');
        
        // 현재 접근 가능한 페이지 ID 목록
        const currentPageIds = window.currentAccess.map(page => page.PAGE_ID);
        
        // 추가 가능한 페이지 필터링 (현재 접근 가능한 페이지 제외)
        const availablePages = window.allPages.filter(page => 
            !currentPageIds.includes(page.PAGE_ID)
        );

        if (availablePages.length === 0) {
            $container.html('<div class="empty-message">추가 가능한 페이지가 없습니다.</div>');
            return;
        }

        const html = availablePages.map(page => `
            <div class="page-item available">
                <div class="page-info">
                    <div class="page-name">${page.PAGE_NAME}</div>
                    <div class="page-menu">${page.MENU_NAME}</div>
                </div>
                <button class="page-action add-btn" data-page-id="${page.PAGE_ID}">추가</button>
            </div>
        `).join('');
        
        $container.html(html);
    }

    // 페이지를 역할에 추가
    function addPageToRole(pageId) {
        const page = window.allPages.find(p => p.PAGE_ID == pageId);
        if (page && !window.currentAccess.find(p => p.PAGE_ID == pageId)) {
            window.currentAccess.push(page);
            updateAccessDisplay();
        }
    }

    // 페이지를 역할에서 제거
    function removePageFromRole(pageId) {
        window.currentAccess = window.currentAccess.filter(page => page.PAGE_ID != pageId);
        updateAccessDisplay();
    }

    // 변경사항 저장
    function saveAccessChanges() {
        if (!window.selectedRoleId) {
            alert('권한을 선택해주세요.');
            return;
        }

        const $button = $('#saveBtn');
        const originalText = $button.text();
        $button.text('저장 중...').prop('disabled', true);

        const accessData = {
            roleId: window.selectedRoleId,
            pageIds: window.currentAccess.map(page => page.PAGE_ID)
        };

        $.ajax({
            url: '/api/access',
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(accessData),
            success: function(response) {
                if (response.success) {
                    alert('접근 권한이 성공적으로 저장되었습니다.');
                    window.originalAccess = [...window.currentAccess];
                } else {
                    alert(response.message || '저장 중 오류가 발생했습니다.');
                }
            },
            error: function(xhr, status, error) {
                console.error('접근 권한 저장 실패:', xhr.responseText);
                let errorMessage = '접근 권한 저장 중 오류가 발생했습니다.';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                
                alert(errorMessage);
            },
            complete: function() {
                $button.text(originalText).prop('disabled', false);
            }
        });
    }

    // 변경사항 초기화
    function resetChanges() {
        if (confirm('변경사항을 모두 초기화하시겠습니까?')) {
            window.currentAccess = [...window.originalAccess];
            updateAccessDisplay();
        }
    }

    // 에러 메시지 표시
    function showError(message) {
        $('#currentPages, #availablePages').html(`<div class="empty-message">${message}</div>`);
    }
}