$(document).ready(function() {
   // 초기화
   if (!checkUserLogin()) return;

   // 전역 변수 추가
   window.passwordChangeRequired = false;

   // 자동 로그아웃 초기화
   initAutoLogout();
   
   // 세션 만료 체크 초기화
   initSessionExpiryCheck();

   // 비밀번호 변경 강제 체크
   checkForcePasswordChange();
   
   // 사용자 로그인 확인
   function checkUserLogin() {
       const currentUser = localStorage.getItem('currentUser');
       
       if (!currentUser) {
           alert('로그인이 필요합니다.');
           window.location.href = '/login';
           return false;
       }
       
       try {
           const user = JSON.parse(currentUser);
           
           // 세션 만료 체크
           if (user.expiresAt) {
               const expiresAt = new Date(user.expiresAt);
               const now = new Date();
               
               if (now > expiresAt) {
                   // 세션 만료
                   alert('세션이 만료되었습니다. 다시 로그인해주세요.');
                   localStorage.removeItem('currentUser');
                   window.location.href = '/login';
                   return false;
               }
           }
           
           displayUserInfo(user);
           loadMenu(user.roleId);
           return true;
       } catch (error) {
           console.error('사용자 정보 파싱 오류:', error);
           logout();
           return false;
       }
   }

   // ! 세션 만료 시간 리셋 함수
   function resetSessionExpiry() {
       const currentUser = localStorage.getItem('currentUser');
       if (currentUser) {
           try {
               const user = JSON.parse(currentUser);
               const now = new Date();
               const newExpiresAt = new Date(now.getTime() + 5 * 60 * 1000); // 현재 시간 + 5분
               
               user.expiresAt = newExpiresAt.toISOString();
               localStorage.setItem('currentUser', JSON.stringify(user));
               
               console.log('세션 만료 시간이 리셋되었습니다:', newExpiresAt);
           } catch (error) {
               console.error('세션 리셋 오류:', error);
           }
       }
   }

   // ! 세션 만료 자동 체크 함수
   function initSessionExpiryCheck() {
       // 30초마다 세션 만료 체크
       const sessionCheckInterval = setInterval(() => {
           const currentUser = localStorage.getItem('currentUser');
           if (currentUser) {
               try {
                   const user = JSON.parse(currentUser);
                   if (user.expiresAt) {
                       const expiresAt = new Date(user.expiresAt);
                       const now = new Date();
                       
                       if (now > expiresAt) {
                           clearInterval(sessionCheckInterval);
                           performAutoLogout('session_expired');
                       }
                   }
               } catch (error) {
                   console.error('세션 체크 오류:', error);
               }
           } else {
               clearInterval(sessionCheckInterval);
           }
       }, 30000); // 30초마다 체크
       
       // 정리 함수에 세션 체크 인터벌 추가
       if (!window.autoLogoutCleanup) {
           window.autoLogoutCleanup = function() {};
       }
       
       const originalCleanup = window.autoLogoutCleanup;
       window.autoLogoutCleanup = function() {
           originalCleanup();
           clearInterval(sessionCheckInterval);
       };
   }

   // ! 코멘트 모달 표시
   function showCommentModal(onCloseCallback) {
       createCommentModal();
       initCommentModalEvents(onCloseCallback);
       $('#commentModal').addClass('active');
   }

   // ! 코멘트 모달 초기화
   function initCommentModalEvents(onCloseCallback) {
       // 모달 닫기 함수
       window.closeCommentModal = function() {
           $('#commentModal').removeClass('active');
           setTimeout(() => {
               $('#commentModal').remove();
               
               // 콜백 함수 실행
               if (onCloseCallback && typeof onCloseCallback === 'function') {
                   onCloseCallback();
               }
           }, 300);
       };

       // 글자 수 계산 (단순화)
       function updateCharacterCounter() {
           const text = $('#commentText').val();
           const charLength = text.length;
           const maxChars = 333;
           const counter = $('#charCount');
           
           counter.text(`${charLength} / ${maxChars}자`);
           
           // 글자 수에 따른 색상 변경
           if (charLength > maxChars) {
               counter.addClass('danger').removeClass('warning');
               $('#commentText').addClass('over-limit');
           } else if (charLength > maxChars * 0.9) {
               counter.addClass('warning').removeClass('danger');
               $('#commentText').removeClass('over-limit');
           } else {
               counter.removeClass('warning danger');
               $('#commentText').removeClass('over-limit');
           }
       }

       // 이벤트 리스너 등록
       $(document).off('input.commentModal').on('input.commentModal', '#commentText', function() {
           updateCharacterCounter();
           
           // 텍스트 영역 자동 높이 조절
           this.style.height = 'auto';
           this.style.height = Math.max(120, this.scrollHeight) + 'px';
       });

       // 저장 버튼 클릭
       $(document).off('click.commentModal', '#saveCommentBtn').on('click.commentModal', '#saveCommentBtn', function() {
           const comment = $('#commentText').val().trim();
           
           if (!comment) {
               alert('코멘트를 입력해주세요.');
               return;
           }
           
           if (comment.length > 333) {
               alert('코멘트는 최대 333자까지 입력 가능합니다.');
               return;
           }
           
           // 로딩 상태 표시
           const $button = $(this);
           $button.addClass('loading').prop('disabled', true);
           
           const currentUser = JSON.parse(localStorage.getItem('currentUser'));
           
           // 코멘트 저장 API 호출
           $.ajax({
               url: '/api/comments',
               method: 'POST',
               contentType: 'application/json',
               data: JSON.stringify({
                   content: comment,
                   userId: currentUser.userId,
                   loginHistoryId: currentUser.loginHistoryId
               }),
               success: function(response) {
                   if (response.success) {
                       alert('코멘트가 저장되었습니다.');
                       closeCommentModal();
                   } else {
                       alert(response.message || '코멘트 저장 중 오류가 발생했습니다.');
                   }
               },
               error: function(xhr, status, error) {
                   console.error('코멘트 저장 실패:', error);
                   alert('코멘트 저장 중 오류가 발생했습니다.');
               },
               complete: function() {
                   $button.removeClass('loading').prop('disabled', false);
               }
           });
       });

       // 취소 버튼 클릭
       $(document).off('click.commentModal', '#cancelCommentBtn').on('click.commentModal', '#cancelCommentBtn', function() {
           const comment = $('#commentText').val().trim();
           
           if (comment) {
               if (confirm('입력한 내용이 저장되지 않습니다. 정말 취소하시겠습니까?')) {
                   closeCommentModal();
               }
           } else {
               closeCommentModal();
           }
       });

       // ESC 키로 모달 닫기
       $(document).off('keydown.commentModal').on('keydown.commentModal', function(e) {
           if (e.key === 'Escape' && $('#commentModal').hasClass('active')) {
               $('#cancelCommentBtn').click();
           }
       });

       // 모달 오버레이 클릭 방지
       $(document).off('click.commentModal', '.modal-overlay').on('click.commentModal', '.modal-overlay', function(e) {
           if (e.target === this) {
               // 모달 외부 클릭 시에도 완전히 차단
               e.preventDefault();
               e.stopPropagation();
           }
       });

       // 포커스 효과
       $(document).off('focus.commentModal blur.commentModal', '#commentText')
           .on('focus.commentModal', '#commentText', function() {
               $(this).parent().css('transform', 'scale(1.02)');
           })
           .on('blur.commentModal', '#commentText', function() {
               $(this).parent().css('transform', 'scale(1)');
           });

       // 초기 카운터 업데이트
       updateCharacterCounter();
   }

   // ! 코멘트 모달 생성
   function createCommentModal() {
       // 기존 모달이 있으면 제거
       $('#commentModal').remove();
       
       const modalHtml = `
           <!-- 코멘트 모달 HTML -->
           <div class="modal-overlay" id="commentModal">
               <div class="comment-modal">
                   <div class="modal-header"></div>
                   
                   <div class="modal-title-section">
                       <h2 class="modal-title">코멘트 입력</h2>
                       <p class="modal-subtitle">시스템 사용에 대한 코멘트를 입력해주세요.</p>
                   </div>
                   
                   <div class="modal-body">
                       <form class="comment-form" id="commentForm">
                           <div class="comment-form-group">
                               <label class="comment-form-label">코멘트</label>
                               <textarea 
                                   class="comment-form-textarea" 
                                   id="commentText" 
                                   placeholder="코멘트를 입력해주세요..."
                                   rows="5"
                                   maxlength="333"
                               ></textarea>
                               <div class="character-counter">
                                   <span class="counter-text">입력 가능한 글자 수</span>
                                   <span class="counter-numbers" id="charCount">0 / 333자</span>
                               </div>
                           </div>
                       </form>
                   </div>
                   
                   <div class="modal-footer">
                       <button type="button" class="comment-btn comment-btn-primary" id="saveCommentBtn">저장</button>
                       <button type="button" class="comment-btn comment-btn-secondary" id="cancelCommentBtn">취소</button>
                   </div>
               </div>
           </div>
       `;
       
       $('body').append(modalHtml);
   }

   // ! 비밀번호 변경 강제 체크
   function checkForcePasswordChange() {
       const currentUser = JSON.parse(localStorage.getItem('currentUser'));

       // 비밀번호 변경 필요 여부를 전역 변수에 저장
       window.passwordChangeRequired = currentUser.passwordChangeRequired;

       // 모든 경우에 코멘트 모달을 먼저 표시
       setTimeout(() => {
           showCommentModal(() => {
               // 코멘트 모달이 닫힌 후 비밀번호 변경 필요 여부 확인
               if (currentUser.passwordChangeRequired) {
                   setTimeout(() => {
                       loadPage('password-change');
                       alert(currentUser.passwordChangeReason);
                       // 사이드바 비활성화
                       updateSidebarState();
                   }, 300);
               }
           });
       }, 500);
   }

   function displayUserInfo(user) {
       $('.user-role').text(user.roleName);
       $('.user-id').text(user.userId);
       $('.user-name').text(user.name);
   }

   // ! 권한 정보 로딩
   function loadMenu(roleId) {
       $.ajax({
           url: `/api/access/${roleId}`,
           method: 'GET',
           success: function(response) {
               if (response.success) {
                   window.userPages = response.data.pages;
                   generateDynamicMenu(window.userPages);
                   setupEventListeners();
               } else {
                   showMenuError('권한 정보를 불러올 수 없습니다.');
               }
           },
           error: function(xhr, status, error) {
               console.error('권한 조회 오류:', error);
               showMenuError('메뉴 로딩 중 오류가 발생했습니다.');
           }
       });
   }

   function generateDynamicMenu(pages) {
       const menuContainer = $('#dynamicMenu');

       // 메뉴 그룹핑
       const menuGroups = groupPagesByMenu(pages);
       
       // 메뉴 HTML 생성
       Object.keys(menuGroups).forEach(menuName => {
           const menuId = createMenuId(menuName);
           const menuHtml = createMenuSectionHtml(menuName, menuId, menuGroups[menuName]);
           menuContainer.append(menuHtml);
       });
   }

   function groupPagesByMenu(pages) {
       const groups = {};
       
       pages.forEach(page => {
           const menuName = page.MENU_NAME;
           if (!groups[menuName]) {
               groups[menuName] = [];
           }
           groups[menuName].push(page);
       });
       
       return groups;
   }

   function createMenuId(menuName) {
       return menuName.replace(/\s+/g, '-').toLowerCase() + '-menu';
   }

   function createMenuSectionHtml(menuName, menuId, pages) {
       const subMenuItems = pages.map(page => 
           `<div class="sub-menu-item" data-page="${page.PAGE_LINK}">${page.PAGE_NAME}</div>`
       ).join('');
       
       return `
           <div class="menu-section">
               <div class="main-menu" data-target="${menuId}">
                   ${menuName}
                   <span class="menu-arrow">▶</span>
               </div>
               <div class="sub-menu" id="${menuId}">
                   ${subMenuItems}
               </div>
           </div>
       `;
   }

   function showMenuError(message) {
       $('#dynamicMenu').html(`<div class="menu-error">${message}</div>`);
   }

   function setupEventListeners() {
       // 햄버거 메뉴
       $('#hamburger').click(() => {
           if (window.passwordChangeRequired) {
               alert('비밀번호를 먼저 변경해주세요.');
               return;
           }
           toggleSidebar();
       });
       $('#sidebarOverlay').click(() => closeSidebar());

       // 로그아웃 버튼
       $('#logoutBtn').click(() => logout());
       
       // 동적 메뉴 이벤트
       $(document).on('click', '.main-menu', function() {
           if (window.passwordChangeRequired) {
               alert('비밀번호를 먼저 변경해주세요.');
               return;
           }
           toggleMainMenu($(this));
       });
       
       $(document).on('click', '.sub-menu-item', function() {
           const page = $(this).data('page');
           if (window.passwordChangeRequired && page !== 'password-change') {
               alert('비밀번호를 먼저 변경해주세요.');
               return;
           }
           handlePageNavigation(page);
       });
       
       // 키보드/윈도우 이벤트
       $(window).resize(() => {
           if (window.innerWidth > 768) closeSidebar();
       });
       // ESC 키로 사이드바 닫기
       $(document).keyup((e) => {
           if (e.keyCode === 27) closeSidebar(); // ESC
       });
   }

   function toggleSidebar() {
       const isActive = $('#hamburger').hasClass('active');
       if (isActive) {
           closeSidebar();
       } else {
           $('#hamburger, #sidebar, #sidebarOverlay').addClass('active');
       }
   }

   function closeSidebar() {
       $('#hamburger, #sidebar, #sidebarOverlay').removeClass('active');
       $('.main-menu, .sub-menu').removeClass('active');
       $('.menu-arrow').removeClass('rotated');
   }

   function toggleMainMenu($menu) {
       const target = $menu.data('target');
       const $subMenu = $('#' + target);
       const $arrow = $menu.find('.menu-arrow');
       
       // 다른 메뉴들 닫기
       $('.main-menu').not($menu).removeClass('active');
       $('.sub-menu').not($subMenu).removeClass('active');
       $('.menu-arrow').not($arrow).removeClass('rotated');
       
       // 현재 메뉴 토글
       $menu.toggleClass('active');
       $subMenu.toggleClass('active');
       $arrow.toggleClass('rotated');
   }

   // ! 로그아웃 처리
   function logout() {
       if (confirm('로그아웃 하시겠습니까?')) {
           // 자동 로그아웃 타이머 정리
           if (window.autoLogoutCleanup) {
               window.autoLogoutCleanup();
           }
           
           // 로그아웃 API 호출
           const currentUser = JSON.parse(localStorage.getItem('currentUser'));
           
           $.ajax({
               url: '/api/logout',
               method: 'POST',
               contentType: 'application/json',
               data: JSON.stringify({
                   userId: currentUser.userId,
                   logoutType: 'manual' // 수동 로그아웃 표시
               }),
               success: function(response) {
                   console.log('로그아웃 기록 저장 성공');
               },
               error: function(xhr, status, error) {
                   console.error('로그아웃 기록 저장 실패:', error);
               },
               complete: function() {
                   // 로컬 스토리지 정리
                   localStorage.removeItem('currentUser');

                   // 현재 페이지 정리
                   if (window.currentPageCleanup) {
                       window.currentPageCleanup();
                   }
                   
                   // 로그인 페이지로 이동
                   window.location.href = '/login';
               }
           });
       }
   }

   // ! 자동 로그아웃
   function initAutoLogout() {
       const AUTO_LOGOUT_TIME = 5 * 60 * 1000; // 5분 (밀리초)
       
       let autoLogoutTimer = null;

       // 타이머 리셋 함수 (메뉴 클릭 시에만 호출)
       function resetAutoLogoutTimer() {
           // 기존 타이머 클리어
           if (autoLogoutTimer) {
               clearTimeout(autoLogoutTimer);
           }
           
           // 세션 만료 시간도 함께 리셋
           resetSessionExpiry();
           
           // 자동 로그아웃 타이머 설정 (5분 후)
           autoLogoutTimer = setTimeout(() => {
               performAutoLogout('auto');
           }, AUTO_LOGOUT_TIME);
       }

       // 자동 로그아웃 수행
       function performAutoLogout(reason = 'auto') {
           const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
           
           let logoutType = 'auto';
           let alertMessage = '5분간 활동이 없어 자동 로그아웃되었습니다.';
           
           if (reason === 'session_expired') {
               logoutType = 'session_expired';
               alertMessage = '세션이 만료되어 자동 로그아웃되었습니다.';
           }
           
           $.ajax({
               url: '/api/logout',
               method: 'POST',
               contentType: 'application/json',
               data: JSON.stringify({
                   userId: currentUser.userId,
                   logoutType: logoutType
               }),
               success: function(response) {
                   console.log('자동 로그아웃 기록 저장 성공');
               },
               error: function(xhr, status, error) {
                   console.error('자동 로그아웃 기록 저장 실패:', error);
               },
               complete: function() {
                   localStorage.removeItem('currentUser');

                   // 현재 페이지 정리
                   if (window.currentPageCleanup) {
                       window.currentPageCleanup();
                   }
                   
                   alert(alertMessage);
                   window.location.href = '/login';
               }
           });
       }

       // 로그인 시 타이머 시작
       resetAutoLogoutTimer();

       // 전역 함수로 등록 (메뉴 클릭 시에만 사용)
       window.resetAutoLogoutTimer = resetAutoLogoutTimer;
       
       // 정리 함수 등록
       window.autoLogoutCleanup = function() {
           if (autoLogoutTimer) {
               clearTimeout(autoLogoutTimer);
           }
       };
   }

   function handlePageNavigation(page) {
       try {
           loadPage(page);
           closeSidebar();
       } catch (error) {
           console.error('페이지 로드 중 오류:', error);
           $('.dashboard-container').html('<div class="error-message">페이지를 불러올 수 없습니다.</div>');
       }
   }

   // ! 페이지 로딩
   function loadPage(pageName) {
        // 기존 페이지 정리
        if (window.currentPageCleanup) {
            window.currentPageCleanup();
        }
        
        // 조회 페이지들은 공통 템플릿과 CSS 사용
        const historyPages = [
            'equipment-history', 'alarm-history', 'report-history',
            'login-history', 'user-history', 'data-history', 'audit-trail'
        ];
        
        if (historyPages.includes(pageName)) {
            // 공통 CSS 로드
            if (!$(`link[href*="history-base.css"]`).length) {
                $('head').append(`<link rel="stylesheet" href="static/css/history-base.css">`);
            }
            
            // 공통 HTML 템플릿 로드
            $.get(`static/html/history-base.html`)
                .done(function(data) {
                    $('.dashboard-container').html(data);
                    
                    // 공통 JS와 개별 JS 로드
                    Promise.all([
                        $.getScript(`static/js/history-base.js`),
                        $.getScript(`static/js/${pageName}.js`)
                    ]).then(() => {
                        const functionName = convertToFunctionName(pageName, 'init');
                        if (typeof window[functionName] === 'function') {
                            window[functionName]();
                        }
                    }).catch((error) => {
                        console.error(`${pageName} 스크립트 로드 실패:`, error);
                        $('.dashboard-container').html('<div class="error-message">페이지를 불러올 수 없습니다.</div>');
                    });
                })
                .fail(function() {
                    $('.dashboard-container').html('<div class="error-message">공통 템플릿을 불러올 수 없습니다.</div>');
                });
        } else {
            // 기존 방식으로 개별 페이지 로드 (사용자 관리 등)
            if (!$(`link[href*="${pageName}.css"]`).length) {
                $('head').append(`<link rel="stylesheet" href="static/css/${pageName}.css">`);
            }
            
            $.get(`static/html/${pageName}.html`)
                .done(function(data) {
                    $('.dashboard-container').html(data);
                    
                    $.getScript(`static/js/${pageName}.js`)
                        .done(function() {
                            const functionName = convertToFunctionName(pageName, 'init');
                            if (typeof window[functionName] === 'function') {
                                window[functionName]();
                            }
                        })
                        .fail(function(jqxhr, textStatus, error) {
                            console.error(`${pageName}.js 로드 실패:`, textStatus, error);
                        });
                })
                .fail(function() {
                    $('.dashboard-container').html('<div class="error-message">페이지를 불러올 수 없습니다.</div>');
                });
        }
    }

    function convertToFunctionName(pageName, prefix) {
        const words = pageName.split('-');
        const camelCase = words.map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join('');
        return `${prefix}${camelCase}Page`;
    }

});

// ! 전역 함수로 사이드바 상태 업데이트 함수 노출
window.updateSidebarState = function() {
    const $hamburger = $('#hamburger');
    const $sidebar = $('#sidebar');
    
    if (window.passwordChangeRequired) {
        // 비밀번호 변경 필요시 사이드바 비활성화
        $hamburger.addClass('disabled').attr('title', '비밀번호를 먼저 변경해주세요.');
        $sidebar.addClass('password-required');
        console.log('사이드바 비활성화됨');
    } else {
        // 정상 상태시 사이드바 활성화
        $hamburger.removeClass('disabled').removeAttr('title');
        $sidebar.removeClass('password-required');
        console.log('사이드바 활성화됨');
    }
};

// ! 비밀번호 변경 완료 처리 함수
window.onPasswordChangeSuccess = function() {
    console.log('비밀번호 변경 성공 처리');
    
    // 전역 변수 업데이트
    window.passwordChangeRequired = false;
    
    // localStorage의 사용자 정보 업데이트
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    currentUser.passwordChangeRequired = false;
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    // 사이드바 다시 활성화
    window.updateSidebarState();
    
    // 메인 대시보드로 이동
    setTimeout(() => {
        $('.dashboard-container').html(`
            <div class="logo-placeholder">
                <img src="static/img/logo.png" alt="(주)경남제약 로고">
            </div>
        `);
    }, 500);
};