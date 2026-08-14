new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            currentPage: 1,
            totalPages: 1,
            records: [],
            filteredRecords: [],
            searchKeyword: '',
            startDate: '',
            endDate: ''
        };
    },
    mounted() {
        this.getPageInfo();
        this.loadData();
    },
    methods: {
        getPageInfo() {
            const urlParams = new URLSearchParams(window.location.search);
            this.currentPage = parseInt(urlParams.get('page'), 10) || 1;
            const n = typeof window.__PURCHASE_LIST_TOTAL_PAGES__ !== 'undefined'
                ? parseInt(window.__PURCHASE_LIST_TOTAL_PAGES__, 10)
                : 1;
            this.totalPages = !isNaN(n) && n > 0 ? n : 1;
        },
        loadData() {
            this.records = window.PURCHASE_RECORD_DATA || [];
            this.filteredRecords = this.records;
        },
        search() {
            this.filteredRecords = this.records.filter(record => {
                let matchSupplier = true;
                let matchStartDate = true;
                let matchEndDate = true;

                if (this.searchKeyword && this.searchKeyword.trim() !== '') {
                    matchSupplier = record.supplier_name.toLowerCase().includes(this.searchKeyword.toLowerCase().trim());
                }

                if (this.startDate) {
                    matchStartDate = new Date(record.purchase_time) >= new Date(this.startDate);
                }

                if (this.endDate) {
                    matchEndDate = new Date(record.purchase_time) <= new Date(this.endDate);
                }

                return matchSupplier && matchStartDate && matchEndDate;
            });
        },
        goPage(page) {
            if (page < 1) page = 1;
            if (page > this.totalPages) page = this.totalPages;
            window.location.href = '?page=' + page;
        },
        prevPage() {
            this.goPage(this.currentPage - 1);
        },
        nextPage() {
            this.goPage(this.currentPage + 1);
        },
        lastPage() {
            this.goPage(this.totalPages);
        },
        async deletePurchaseRecord(id) {
            if (!confirm('确定要删除该进货记录吗？删除后无法恢复！')) {
                return;
            }
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            try {
                await axios.post('/purchdel/' + id + '/', {}, {
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                alert('删除成功！');
                location.reload();
            } catch (err) {
                alert('删除失败');
            }
        }
    }
});
