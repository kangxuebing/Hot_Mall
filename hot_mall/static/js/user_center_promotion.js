// 促销商品管理页面JavaScript
new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        promotionList: [],
        currentPage: 1,
        totalPages: 1,
        loading: false,
        keyword: ''
    },
    methods: {
        loadPromotions: function(page) {
            this.loading = true;
            const url = `/pos/promotion/api/list/?page=${page}&keyword=${encodeURIComponent(this.keyword)}`;
            
            fetch(url, {
                headers: {
                    'X-CSRFToken': window.csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.code === 0) {
                    this.promotionList = data.promotions;
                    this.totalPages = data.total_pages;
                    this.currentPage = data.current_page;
                } else {
                    alert('加载失败: ' + data.errmsg);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('加载失败');
            })
            .finally(() => {
                this.loading = false;
            });
        },
        
        formatDate: function(dateTimeStr) {
            if (!dateTimeStr) return '-';
            const date = new Date(dateTimeStr);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        deletePromotion: function(id) {
            if (confirm('确定要删除这个促销商品吗？')) {
                fetch(`/pos/promotion/delete/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': window.csrfToken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.code === 0) {
                        alert('删除成功');
                        this.loadPromotions(this.currentPage);
                    } else {
                        alert('删除失败: ' + data.errmsg);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('删除失败');
                });
            }
        },
        
        goPage: function(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.loadPromotions(page);
            }
        },
        
        prevPage: function() {
            if (this.currentPage > 1) {
                this.loadPromotions(this.currentPage - 1);
            }
        },
        
        nextPage: function() {
            if (this.currentPage < this.totalPages) {
                this.loadPromotions(this.currentPage + 1);
            }
        }
    },
    mounted: function() {
        this.loadPromotions(1);
    }
});