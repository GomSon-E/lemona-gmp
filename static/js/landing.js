$(document).ready(function() {
    // 초기화
    if (!checkUserLogin()) return;
    
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
            displayUserInfo(user);
            loadMenu(user.roleId);
            return true;
        } catch (error) {
            console.error('사용자 정보 파싱 오류:', error);
            logout();
            return false;
        }
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
        $('#hamburger').click(() => toggleSidebar());
        $('#sidebarOverlay').click(() => closeSidebar());
        
        // 동적 메뉴 이벤트
        $(document).on('click', '.main-menu', function() {
            toggleMainMenu($(this));
        });
        
        $(document).on('click', '.sub-menu-item', function() {
            handlePageNavigation($(this).data('page'));
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
        
        // CSS 로드
        if (!$(`link[href*="${pageName}.css"]`).length) {
            $('head').append(`<link rel="stylesheet" href="static/css/${pageName}.css">`);
        }
        
        // HTML 로드
        $.get(`static/html/${pageName}.html`)
            .done(function(data) {
                $('.dashboard-container').html(data);
                
                // JS 로드 및 초기화
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

    // ! 페이지명 -> 함수명 변환
    function convertToFunctionName(pageName, prefix) {
        const words = pageName.split('-');
        const camelCase = words.map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join('');
        return `${prefix}${camelCase}Page`;
    }

});