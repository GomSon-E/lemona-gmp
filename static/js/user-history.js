function initUserHistoryPage() {
    if (window.currentHistoryPage) {
        window.currentHistoryPage.cleanup();
    }
    
    const config = {
        pageTitle: '사용자 관리 이력 조회',
        apiEndpoint: '/api/user-history',
        tableName: 'USER_HISTORY',
        columns: [
            { field: 'CREATE_DT', label: '작업일시', type: 'datetime' },
            { field: 'USER_ID', label: '작업자 ID', type: 'text' },
            { field: 'CONTENT', label: '작업내용', type: 'text' },
            { field: 'COMMENT_CONTENT', label: '코멘트', type: 'text' }
        ],
        filterLabels: {
            period: '작업일시',
            userId: '작업자 ID',
            content: '작업내용',
            comment: '코멘트'
        }
    };
    
    window.currentHistoryPage = new HistoryBasePage(config);
}