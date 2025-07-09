function initLoginHistoryPage() {
    if (window.currentHistoryPage) {
        window.currentHistoryPage.cleanup();
    }
    
    const config = {
        pageTitle: '접속 이력 조회',
        apiEndpoint: '/api/login-history',
        tableName: 'LOGIN_HISTORY',
        columns: [
            { field: 'CREATE_DT', label: '접속일시', type: 'datetime' },
            { field: 'USER_ID', label: '접속자 ID', type: 'text' },
            { field: 'CONTENT', label: '접속내용', type: 'text' },
            { field: 'COMMENT_CONTENT', label: '코멘트', type: 'text' }
        ],
        filterLabels: {
            period: '접속일시',
            userId: '접속자 ID',
            content: '접속내용',
            comment: '코멘트'
        }
    };
    
    window.currentHistoryPage = new HistoryBasePage(config);
}