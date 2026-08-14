$(function () {
    // 使用base.html中的统一#app容器
    const app = document.getElementById('app');
    if (!app) return;
    
    // 检查是否是中奖历史记录页面
    const viewData = app.querySelector('[data-view="lottery-record-list"]');
    if (!viewData) return;
    
    // Vue应用实例
    new Vue({
        el: '#app',
        delimiters: ['[[', ']]'],
        data: {
            records: [],
            currentPage: 1,
            totalPages: 1,
            loading: false,
            searchForm: {
                username: '',
                is_won: '',
                start_date: '',
                end_date: ''
            }
        },
        methods: {
            // 加载中奖记录
            loadLotteryRecords: function(page) {
                this.loading = true;
                const url = '/lottery/api/records/?page=' + page;
                if (this.searchForm.username) url += '&username=' + encodeURIComponent(this.searchForm.username);
                if (this.searchForm.is_won) url += '&is_won=' + this.searchForm.is_won;
                if (this.searchForm.start_date) url += '&start_date=' + this.searchForm.start_date;
                if (this.searchForm.end_date) url += '&end_date=' + this.searchForm.end_date;

                $.ajax({
                    url: url,
                    method: 'GET',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    success: (data) => {
                        if (data.success) {
                            this.records = data.items;
                            this.currentPage = data.current_page;
                            this.totalPages = data.total_pages;
                        } else {
                            alert('获取中奖记录失败');
                        }
                        this.loading = false;
                    },
                    error: (error) => {
                        alert('获取中奖记录失败: ' + error.message);
                        this.loading = false;
                    }
                });
            },
            
            // 搜索中奖记录
            searchRecords: function() {
                this.currentPage = 1;
                this.loadLotteryRecords(1);
            },
            
            // 重置搜索
            resetSearch: function() {
                this.searchForm.username = '';
                this.searchForm.is_won = '';
                this.searchForm.start_date = '';
                this.searchForm.end_date = '';
                this.currentPage = 1;
                this.loadLotteryRecords(1);
            },
            
            // 获取状态样式类
            getStatusClass: function(isWon) {
                return isWon ? 'status-won' : 'status-lost';
            },
            
            // 获取CSRF token
            getCsrfToken: function() {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
        },
        mounted: function() {
            // 页面加载时获取中奖记录
            this.loadLotteryRecords(1);
        }
    });
});
