function initAlarmHistoryPage() {
    if (window.currentHistoryPage) {
        window.currentHistoryPage.cleanup();
    }
    
    const config = {
        pageTitle: '설비 알람 이력 조회',
        apiEndpoint: '/api/alarm-history',
        tableName: 'ALARM_HISTORY',
        columns: [
            { field: 'CREATE_DT', label: '알람일시', type: 'datetime' },
            { field: 'USER_ID', label: '확인자 ID', type: 'text' },
            { field: 'CONTENT', label: '알람내용', type: 'text' },
            { field: 'COMMENT_CONTENT', label: '코멘트', type: 'text' }
        ],
        filterLabels: {
            period: '알람일시',
            userId: '확인자 ID',
            content: '알람내용',
            comment: '코멘트'
        }
    };
    
    window.currentHistoryPage = new HistoryBasePage(config);
}