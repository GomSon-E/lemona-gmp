function initUserUpdatePage() {
    // 기존 이벤트 제거
    $(document).off('click', '#searchBtn, #resetBtn');
    $(document).off('click', '.user-table tbody tr');
    $(document).off('click', '#saveUserBtn, #resetPasswordBtn');
    $(document).off('input change', '.filter-input, .filter-select');

    // 전역 변수
    window.allUsers = [];
    window.filteredUsers = [];
    window.selectedUser = null;
    window.currentUserRole = JSON.parse(localStorage.getItem('currentUser')).roleId;

    // 초기 데이터 로드
    loadUsers();

    // 검색 버튼 이벤트
    $(document).on('click', '#searchBtn', function() {
        applyFilters();
    });

    // 초기화 버튼 이벤트
    $(document).on('click', '#resetBtn', function() {
        resetFilters();
    });

    // 사용자 테이블 행 클릭 이벤트
    $(document).on('click', '.user-table tbody tr', function() {
        if ($(this).find('td').length === 1) return; // 로딩 메시지 행은 제외
        const userId = $(this).data('user-id');
        selectUser(userId);
    });

    // 저장 버튼 이벤트
    $(document).on('click', '#saveUserBtn', function() {
        saveUserChanges();
    });

    // 비밀번호 초기화 버튼 이벤트
    $(document).on('click', '#resetPasswordBtn', function() {
        resetUserPassword();
    });

    // 실시간 필터링 (Enter 키)
    $(document).on('keypress', '.filter-input', function(e) {
        if (e.which === 13) {
            applyFilters();
        }
    });

    // 전체 사용자 목록 로드
    function loadUsers() {
        $('#userTableBody').html('<tr><td colspan="5" class="loading-message">사용자 목록을 불러오는 중...</td></tr>');
        
        $.ajax({
            url: '/api/users',
            method: 'GET',
            success: function(response) {
                if (response.success) {
                    window.allUsers = response.data;
                    window.filteredUsers = [...window.allUsers];
                    displayUsers(window.filteredUsers);
                } else {
                    showError('사용자 목록을 불러올 수 없습니다.');
                }
            },
            error: function(xhr, status, error) {
                console.error('사용자 목록 로드 오류:', error);
                showError('사용자 목록 로드 중 오류가 발생했습니다.');
            }
        });
    }

    // 사용자 목록 표시
    function displayUsers(users) {
        const $userTableBody = $('#userTableBody');
        
        if (users.length === 0) {
            $userTableBody.html('<tr><td colspan="5" class="no-users-message">검색 조건에 맞는 사용자가 없습니다.</td></tr>');
            return;
        }

        const html = users.map(user => `
            <tr data-user-id="${user.USER_ID}">
                <td>${user.USER_ID}</td>
                <td>${user.NAME}</td>
                <td>${user.DIVISION}</td>  <!-- 이 줄 추가 -->
                <td>${user.ROLE_NAME}</td>
                <td>
                    <span class="user-status ${user.STATUS ? 'active' : 'inactive'}">
                        ${user.STATUS ? '활성' : '비활성'}
                    </span>
                </td>
            </tr>
        `).join('');
        
        $userTableBody.html(html);
    }

    // 필터 적용
    function applyFilters() {
        const filters = {
            userId: $('#filterUserId').val().toLowerCase(),
            userName: $('#filterUserName').val().toLowerCase(),
            division: $('#filterDivision').val().toLowerCase(),
            status: $('#filterStatus').val(),
            role: $('#filterRole').val()
        };

        window.filteredUsers = window.allUsers.filter(user => {
            return (
                (!filters.userId || user.USER_ID.toLowerCase().includes(filters.userId)) &&
                (!filters.userName || user.NAME.toLowerCase().includes(filters.userName)) &&
                (!filters.division || user.DIVISION.toLowerCase().includes(filters.division)) &&
                (!filters.status || user.STATUS.toString() === filters.status) &&
                (!filters.role || user.ROLE_ID.toString() === filters.role)
            );
        });

        displayUsers(window.filteredUsers);
        clearUserSelection();
    }

    // 필터 초기화
    function resetFilters() {
        $('#filterUserId, #filterUserName, #filterDivision').val('');
        $('#filterStatus, #filterRole').val('');
        window.filteredUsers = [...window.allUsers];
        displayUsers(window.filteredUsers);
        clearUserSelection();
    }

    // 사용자 선택
    function selectUser(userId) {
        const user = window.filteredUsers.find(u => u.USER_ID === userId);
        if (!user) return;

        window.selectedUser = user;
        
        // UI 업데이트
        $('.user-table tbody tr').removeClass('selected');
        $(`.user-table tbody tr[data-user-id="${userId}"]`).addClass('selected');
        
        displayUserDetail(user);
    }

    // 사용자 상세 정보 표시
    function displayUserDetail(user) {
        const html = `
            <form class="user-detail-form" id="userDetailForm">
                <div class="form-row">
                    <div class="detail-form-group">
                        <label class="detail-form-label">사용자 ID</label>
                        <input type="text" class="detail-form-input" value="${user.USER_ID}" disabled>
                    </div>
                    
                    <div class="detail-form-group">
                        <label class="detail-form-label">사용자명</label>
                        <input type="text" class="detail-form-input" id="detailUserName" value="${user.NAME}" required>
                    </div>
                    
                    <div class="detail-form-group">
                        <label class="detail-form-label">부서</label>
                        <input type="text" class="detail-form-input" id="detailDivision" value="${user.DIVISION}" required>
                    </div>
                    
                    <div class="detail-form-group">
                        <label class="detail-form-label">상태</label>
                        <select class="detail-form-select" id="detailStatus" required>
                            <option value="1" ${user.STATUS ? 'selected' : ''}>활성</option>
                            <option value="0" ${!user.STATUS ? 'selected' : ''}>비활성</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="detail-form-group">
                        <label class="detail-form-label">권한</label>
                        <select class="detail-form-select" id="detailRole" required>
                            <option value="2" ${user.ROLE_ID === 2 ? 'selected' : ''}>ADMIN</option>
                            <option value="3" ${user.ROLE_ID === 3 ? 'selected' : ''}>MANAGER</option>
                            <option value="4" ${user.ROLE_ID === 4 ? 'selected' : ''}>USER</option>
                        </select>
                    </div>
                    
                    <div class="detail-form-group">
                        <label class="detail-form-label">생성일</label>
                        <div class="detail-form-display">${formatDate(user.CREATE_DT)}</div>
                    </div>
                    
                    <div class="detail-form-group">
                        <label class="detail-form-label">수정일</label>
                        <div class="detail-form-display">${formatDate(user.UPDATE_DT)}</div>
                    </div>
                    
                    <div class="detail-form-group">
                        <label class="detail-form-label">비밀번호 변경일</label>
                        <div class="detail-form-display">${formatDate(user.PW_UPDATE_DT)}</div>
                    </div>
                </div>

                <div class="detail-button-group">
                    <button type="button" class="btn-detail btn-primary" id="saveUserBtn">저장</button>
                    <button type="button" class="btn-detail btn-danger" id="resetPasswordBtn">비밀번호 초기화</button>
                </div>
            </form>
        `;
        
        $('#userDetailContainer').html(html);
    }

    // 사용자 정보 저장
    function saveUserChanges() {
        if (!window.selectedUser) {
            alert('사용자를 선택해주세요.');
            return;
        }

        const formData = {
            name: $('#detailUserName').val(),
            division: $('#detailDivision').val(),
            status: $('#detailStatus').val(),
            roleId: $('#detailRole').val()
        };

        // 유효성 검사
        if (!formData.name || !formData.division || !formData.roleId) {
            alert('모든 필드를 입력해주세요.');
            return;
        }

        const $button = $('#saveUserBtn');
        const originalText = $button.text();
        $button.text('저장 중...').prop('disabled', true);

        $.ajax({
            url: `/api/users/${window.selectedUser.USER_ID}`,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.success) {
                    alert('사용자 정보가 성공적으로 저장되었습니다.');
                    loadUsers(); // 목록 새로고침
                    // 선택된 사용자 정보 업데이트
                    window.selectedUser = { ...window.selectedUser, ...formData };
                } else {
                    alert(response.message || '저장 중 오류가 발생했습니다.');
                }
            },
            error: function(xhr, status, error) {
                console.error('사용자 정보 저장 실패:', xhr.responseText);
                let errorMessage = '사용자 정보 저장 중 오류가 발생했습니다.';
                
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

    // 비밀번호 초기화
    function resetUserPassword() {
        if (!window.selectedUser) {
            alert('사용자를 선택해주세요.');
            return;
        }

        if (!confirm(`${window.selectedUser.USER_ID} 사용자의 비밀번호를 초기화하시겠습니까?\n초기화된 비밀번호는 "1234!" 입니다.`)) {
            return;
        }

        const $button = $('#resetPasswordBtn');
        const originalText = $button.text();
        $button.text('초기화 중...').prop('disabled', true);

        $.ajax({
            url: '/api/users/password/reset',
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({
                userId: window.selectedUser.USER_ID
            }),
            success: function(response) {
                if (response.success) {
                    alert(`${window.selectedUser.USER_ID} 사용자의 비밀번호가 초기화되었습니다.\n초기 비밀번호: 1234!`);
                    loadUsers(); // 목록 새로고침
                } else {
                    alert(response.message || '비밀번호 초기화 중 오류가 발생했습니다.');
                }
            },
            error: function(xhr, status, error) {
                console.error('비밀번호 초기화 실패:', xhr.responseText);
                let errorMessage = '비밀번호 초기화 중 오류가 발생했습니다.';
                
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

    // 사용자 선택 해제
    function clearUserSelection() {
        window.selectedUser = null;
        $('.user-item').removeClass('selected');
        $('#userDetailContainer').html('<div class="no-selection-message">사용자를 선택해주세요</div>');
    }

    // 날짜 포맷팅
    function formatDate(dateString) {
        if (!dateString) return '없음';
        
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        
        return `${year}-${month}-${day}`;
    }

    // 에러 메시지 표시
    function showError(message) {
        $('#userList').html(`<div class="loading-message">${message}</div>`);
    }
}