// static/js/history-base.js
class HistoryBasePage {
    constructor(config) {
        // 설정 정보
        this.config = {
            pageTitle: '조회 페이지',
            apiEndpoint: '/api/history',
            tableName: 'HISTORY',
            columns: [],
            searchFields: ['USER_ID', 'CONTENT', 'COMMENT'],
            filterLabels: {
                period: '기간',
                userId: '사용자 ID',
                content: '작업내용',
                comment: '코멘트'
            },
            autoRefreshInterval: 5000, // 5초
            ...config
        };
        
        // 상태 관리
        this.autoRefreshTimer = null;
        this.currentFilters = {};
        this.lastUpdateTime = null; // 마지막 업데이트 시간 추가
        this.isInitialLoad = true; // 초기 로드 여부
        
        this.init();
    }
    
    init() {
        this.setupUI();
        this.bindEvents();
        this.loadInitialData();
        this.startAutoRefresh();
    }
    
    setupUI() {
        // 페이지 제목 설정
        $('#pageTitle').text(this.config.pageTitle);

        // 필터 라벨 설정
        this.updateFilterLabels();
        
        // 테이블 헤더 생성
        this.createTableHeader();
        
        // 기본 날짜 설정 (최근 30일)
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        $('#endDate').val(this.formatDate(today));
        $('#startDate').val(this.formatDate(thirtyDaysAgo));
    }

    updateFilterLabels() {
        // 기간 라벨 업데이트
        if (this.config.filterLabels.period) {
            $('#periodLabel').text(this.config.filterLabels.period);
        }
        
        // 사용자 ID 라벨 업데이트
        if (this.config.filterLabels.userId) {
            $('label[for="filterUserId"]').text(this.config.filterLabels.userId);
            $('#filterUserId').attr('placeholder', `${this.config.filterLabels.userId} 검색`);
        }
        
        // 작업내용 라벨 업데이트
        if (this.config.filterLabels.content) {
            $('label[for="filterContent"]').text(this.config.filterLabels.content);
            $('#filterContent').attr('placeholder', `${this.config.filterLabels.content} 검색`);
        }
        
        // 코멘트 라벨 업데이트
        if (this.config.filterLabels.comment) {
            $('label[for="filterComment"]').text(this.config.filterLabels.comment);
            $('#filterComment').attr('placeholder', `${this.config.filterLabels.comment} 검색`);
        }
    }
    
    createTableHeader() {
        const headerHtml = this.config.columns.map(col => 
            `<th>${col.label}</th>`
        ).join('');
        $('#tableHeader').html(`<tr>${headerHtml}</tr>`);
    }
    
    bindEvents() {
        // 기존 이벤트 제거
        $(document).off('click.historyBase change.historyBase input.historyBase');
        
        // 검색 버튼
        $(document).on('click.historyBase', '#searchBtn', () => {
            this.search();
        });
        
        // 초기화 버튼
        $(document).on('click.historyBase', '#resetBtn', () => {
            this.resetFilters();
        });
        
        // 보고서 추출 버튼
        $(document).on('click.historyBase', '#exportBtn', () => {
            this.exportReport();
        });
        
        // 자동 새로고침 체크박스
        $(document).on('change.historyBase', '#autoRefresh', (e) => {
            if (e.target.checked) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
        
        // Enter 키 검색
        $(document).on('keypress.historyBase', '.filter-input', (e) => {
            if (e.which === 13) {
                this.search();
            }
        });
    }
    
    loadInitialData() {
        this.search();
    }
    
    search() {
        this.isInitialLoad = true; // 검색할 때는 전체 새로고침
        this.lastUpdateTime = null;
        this.currentFilters = this.getFilters();
        this.loadData();
    }
    
    getFilters() {
        return {
            startDate: $('#startDate').val(),
            endDate: $('#endDate').val(),
            userId: $('#filterUserId').val().trim(),
            content: $('#filterContent').val().trim(),
            comment: $('#filterComment').val().trim()
        };
    }
    
    resetFilters() {
        $('.filter-input').val('');
        
        // 기본 날짜 재설정
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        $('#endDate').val(this.formatDate(today));
        $('#startDate').val(this.formatDate(thirtyDaysAgo));
        
        // 초기화시에는 전체 새로고침
        this.search();
    }
    
    loadData() {
        if (this.isInitialLoad) {
            this.showLoading();
        }
        
        // 증분 업데이트용 파라미터 추가
        const params = {
            ...this.currentFilters,
            lastUpdateTime: this.lastUpdateTime,
            incremental: !this.isInitialLoad
        };
        
        $.ajax({
            url: this.config.apiEndpoint,
            method: 'GET',
            data: params,
            success: (response) => {
                if (response.success) {
                    if (this.isInitialLoad) {
                        // 초기 로드: 전체 데이터 표시
                        this.displayData(response.data);
                        this.updateRecordCount(response.data.length);
                        this.isInitialLoad = false;
                    } else {
                        // 증분 업데이트: 새로운 데이터만 추가
                        if (response.data && response.data.length > 0) {
                            const addedCount = this.addNewData(response.data);
                            if (addedCount > 0) {
                                this.updateRecordCount(this.getCurrentRecordCount());
                                console.log(`새로운 데이터 ${addedCount}건 추가됨`);
                            }
                        }
                    }
                    
                    // 마지막 업데이트 시간 갱신 (서버 시간 사용)
                    if (response.serverTime) {
                        this.lastUpdateTime = response.serverTime;
                    } else {
                        // 백업으로 클라이언트 시간 사용 (MySQL 형식)
                        const now = new Date();
                        this.lastUpdateTime = now.getFullYear() + '-' + 
                                           String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                                           String(now.getDate()).padStart(2, '0') + ' ' + 
                                           String(now.getHours()).padStart(2, '0') + ':' + 
                                           String(now.getMinutes()).padStart(2, '0') + ':' + 
                                           String(now.getSeconds()).padStart(2, '0');
                    }
                } else {
                    this.showError(response.message);
                }
            },
            error: (xhr, status, error) => {
                console.error('데이터 로드 실패:', error);
                this.showError('데이터를 불러오는 중 오류가 발생했습니다.');
            }
        });
    }
    
    // 새로운 데이터를 테이블 상단에 추가
    addNewData(newData) {
        const $tbody = $('#tableBody');
        
        // 기존에 "데이터 없음" 메시지가 있다면 제거
        if ($tbody.find('.no-data-message').length > 0) {
            $tbody.empty();
        }
        
        // 새로운 행들 생성
        const newRows = newData.map(row => {
            const cells = this.config.columns.map(col => {
                let value = row[col.field] || '';
                
                // 데이터 포맷팅
                if (col.type === 'datetime' && value) {
                    value = this.formatDateTime(value);
                } else if (col.type === 'date' && value) {
                    value = this.formatDate(value);
                }
                
                return `<td>${value}</td>`;
            }).join('');
            
            return `<tr class="new-row" style="background-color: #e8f5e8;">${cells}</tr>`;
        }).join('');
        
        // 테이블 상단에 새로운 행들 추가 (최신 데이터가 위에 오도록)
        $tbody.prepend(newRows);
        
        // 새로운 행 강조 효과 (3초 후 일반 색상으로 변경)
        setTimeout(() => {
            $('.new-row').removeClass('new-row').css('background-color', '');
        }, 3000);
        
        // 부드러운 애니메이션 효과
        $tbody.find('tr:lt(' + newData.length + ')').hide().fadeIn(500);
    }
    
    // 현재 테이블의 레코드 수 반환
    getCurrentRecordCount() {
        const $tbody = $('#tableBody');
        return $tbody.find('tr').not('.loading-message, .no-data-message').length;
    }
    
    displayData(data) {
        const $tbody = $('#tableBody');
        
        if (!data || data.length === 0) {
            $tbody.html('<tr><td colspan="100%" class="no-data-message">조회된 데이터가 없습니다.</td></tr>');
            return;
        }
        
        const rows = data.map(row => {
            const cells = this.config.columns.map(col => {
                let value = row[col.field] || '';
                
                // 데이터 포맷팅
                if (col.type === 'datetime' && value) {
                    value = this.formatDateTime(value);
                } else if (col.type === 'date' && value) {
                    value = this.formatDate(value);
                }
                
                return `<td>${value}</td>`;
            }).join('');
            
            return `<tr>${cells}</tr>`;
        }).join('');
        
        // 초기 로드시에만 fade 효과
        $tbody.fadeOut(200, function() {
            $(this).html(rows).fadeIn(200);
        });
    }
    
    updateRecordCount(total) {
        $('#recordCount').text(total.toLocaleString());
    }
    
    showLoading() {
        const $tbody = $('#tableBody');
        const colCount = this.config.columns.length;
        $tbody.fadeOut(200, function() {
            $(this).html(`<tr><td colspan="${colCount}" class="loading-message">데이터를 불러오는 중...</td></tr>`).fadeIn(200);
        });
    }
    
    showError(message) {
        const $tbody = $('#tableBody');
        const colCount = this.config.columns.length;
        $tbody.fadeOut(200, function() {
            $(this).html(`<tr><td colspan="${colCount}" class="no-data-message">오류: ${message}</td></tr>`).fadeIn(200);
        });
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh(); // 기존 타이머 정리
        
        if ($('#autoRefresh').is(':checked')) {
            this.autoRefreshTimer = setInterval(() => {
                this.loadData();
            }, this.config.autoRefreshInterval);
        }
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
        }
    }
    
    exportReport() {
        const filters = this.getFilters();
        
        // 현재 사용자 정보 추가
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
        filters.currentUserId = currentUser.userId || 'unknown';
        filters.loginHistoryId = currentUser.loginHistoryId || null;  // 로그인 히스토리 ID 추가
        
        // 로딩 상태 표시
        const $button = $('#exportBtn');
        const originalText = $button.text();
        $button.text('생성 중...').prop('disabled', true);
        
        // 보고서 추출 API 호출
        const params = new URLSearchParams(filters);
        const url = `${this.config.apiEndpoint}/export?${params}`;
        
        // Fetch API로 PDF 다운로드
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('보고서 생성에 실패했습니다.');
                }
                
                // 응답 헤더에서 파일명 추출
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = `${this.config.pageTitle}_보고서.pdf`; // 기본 파일명
                
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/);
                    if (filenameMatch) {
                        filename = decodeURIComponent(filenameMatch[1]);
                    }
                }
                
                return response.blob().then(blob => ({ blob, filename }));
            })
            .then(({ blob, filename }) => {
                // PDF 파일 다운로드
                const downloadUrl = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename;
                
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // URL 객체 해제
                window.URL.revokeObjectURL(downloadUrl);
                
                console.log('보고서 다운로드 완료:', filename);
            })
            .catch(error => {
                console.error('보고서 생성 실패:', error);
                alert('보고서 생성 중 오류가 발생했습니다.');
            })
            .finally(() => {
                // 버튼 상태 복원
                $button.text(originalText).prop('disabled', false);
            });
    }
        
    // 유틸리티 메서드들
    formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    formatDateTime(datetime) {
        if (!datetime) return '';
        const d = new Date(datetime);

        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hour = String(d.getHours()).padStart(2, '0');
        const minute = String(d.getMinutes()).padStart(2, '0');
        const second = String(d.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
    }
    
    // 정리 메서드
    cleanup() {
        this.stopAutoRefresh();
        $(document).off('.historyBase');
    }
}

// 전역 정리 함수 등록
window.currentPageCleanup = function() {
    if (window.currentHistoryPage) {
        window.currentHistoryPage.cleanup();
        window.currentHistoryPage = null;
    }
};