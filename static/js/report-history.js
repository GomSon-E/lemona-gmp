function initReportHistoryPage() {
    if (window.currentHistoryPage) {
        window.currentHistoryPage.cleanup();
    }
    
    const config = {
        pageTitle: '보고서 생성 이력 조회',
        apiEndpoint: '/api/report-history',
        tableName: 'REPORT_HISTORY',
        columns: [
            { field: 'CREATE_DT', label: '생성일시', type: 'datetime' },
            { field: 'USER_ID', label: '생성자 ID', type: 'text' },
            { field: 'CONTENT', label: '작업내용', type: 'text' },
            { field: 'COMMENT_CONTENT', label: '코멘트', type: 'text' }
        ],
        filterLabels: {
            period: '생성일시',
            userId: '생성자 ID',
            content: '작업내용',
            comment: '코멘트'
        }
    };
    
    window.currentHistoryPage = new HistoryBasePage(config);
}