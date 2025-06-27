$(document).ready(function() {
    // 사이드바 닫기 함수
    function closeSidebar() {
        $('#hamburger').removeClass('active');
        $('#sidebar').removeClass('active');
        $('#sidebarOverlay').removeClass('active');
        
        // 모든 메뉴 닫기
        $('.main-menu').removeClass('active');
        $('.sub-menu').removeClass('active');
        $('.menu-arrow').removeClass('rotated');
    }

    // 햄버거 메뉴 클릭
    $('#hamburger').click(function() {
        if ($(this).hasClass('active')) {
            closeSidebar();
        } else {
            $(this).addClass('active');
            $('#sidebar').addClass('active');
            $('#sidebarOverlay').addClass('active');
        }
    });

    // 사이드바 오버레이 클릭시 사이드바 닫기
    $('#sidebarOverlay').click(function() {
        closeSidebar();
    });

    // 메인 메뉴 클릭
    $('.main-menu').click(function() {
        const target = $(this).data('target');
        const subMenu = $('#' + target);
        const arrow = $(this).find('.menu-arrow');
        
        // 다른 메뉴들 닫기
        $('.main-menu').not(this).removeClass('active');
        $('.sub-menu').not(subMenu).removeClass('active');
        $('.menu-arrow').not(arrow).removeClass('rotated');
        
        // 현재 메뉴 토글
        $(this).toggleClass('active');
        subMenu.toggleClass('active');
        arrow.toggleClass('rotated');
    });

    // 윈도우 리사이즈 대응
    $(window).resize(function() {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });

    // ESC 키로 사이드바 닫기
    $(document).keyup(function(e) {
        if (e.keyCode === 27) { // ESC 키
            closeSidebar();
        }
    });

    // * 서브 메뉴 아이템 클릭
    $('.sub-menu-item').click(function() {
        const page = $(this).data('page');
        console.log('페이지 이동:', page);
        try {
            loadPage(page);
        }
        catch (error) {
            console.error('페이지 로드 중 오류:', error);
            $('.dashboard-container').html('<div class="error-message">페이지를 불러올 수 없습니다.</div>');
        }

        closeSidebar();
    });

    // * 페이지 로딩
    function loadPage(pageName) {
        console.log('loadPage 호출됨, pageName:', pageName);
        
        // 기존 페이지 정리
        if (window.currentPageCleanup) {
            console.log('기존 페이지 정리 중...');
            window.currentPageCleanup();
        }
        
        // CSS 로드
        if (!$(`link[href*="${pageName}.css"]`).length) {
            console.log('CSS 로드 중...');
            $('head').append(`<link rel="stylesheet" href="static/css/${pageName}.css">`);
        }
        
        // HTML 로드
        $.get(`static/html/${pageName}.html`)
            .done(function(data) {
                console.log('HTML 로드 성공');
                $('.dashboard-container').html(data);
                
                // JS 로드 및 초기화
                $.getScript(`static/js/${pageName}.js`)
                    .done(function() {
                        console.log('JS 로드 성공');
                        // 페이지별 초기화 함수 이름
                        const functionName = convertToFunctionName(pageName, 'init');
                        window[functionName]();
                    })
                    .fail(function(jqxhr, textStatus, error) {
                        console.error(`${pageName}.js 로드 실패:`, textStatus, error);
                    });
            })
            .fail(function(jqxhr, textStatus, error) {
                console.error(`${pageName}.html 로드 실패:`, textStatus, error);
                $('.dashboard-container').html('<div class="error-message">페이지를 불러올 수 없습니다.</div>');
            });
    }

    // * 페이지명 -> 함수명 변환
    function convertToFunctionName(pageName, prefix) {
        // 하이픈으로 분리하고 각 단어의 첫 글자를 대문자로 변환
        const words = pageName.split('-');
        const camelCase = words.map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join('');
        
        return `${prefix}${camelCase}Page`;
    }
});