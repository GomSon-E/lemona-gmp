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

    // 서브 메뉴 아이템 클릭
    $('.sub-menu-item').click(function() {
        const page = $(this).data('page');
        
        // 페이지 전환 로직 (여기서는 콘솔에 로그만 출력)
        console.log('페이지 이동:', page);
        
        // 사이드바 닫기
        closeSidebar();
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
});