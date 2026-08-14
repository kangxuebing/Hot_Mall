new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            currentPage: 1,
            totalPages: 1,
            suppliers: [],
            filteredSuppliers: [],
            searchKeyword: ''
        }
    },
    mounted() {
        this.getPageInfo();
        this.loadData();
    },
    methods: {
        getPageInfo() {
            // 从 URL 获取当前页
            const urlParams = new URLSearchParams(window.location.search);
            this.currentPage = parseInt(urlParams.get('page')) || 1;

            // ✅ 修复：从隐藏 input 获取总页数（解决外部JS无法读取Django变量）
            this.totalPages = parseInt(document.getElementById('total_pages').value) || 1;
        },
        loadData() {
            // 从模板变量加载供应商数据
            try {
                // 确保数据是数组格式
                this.suppliers = Array.isArray(window.SUPPLIER_DATA) ? window.SUPPLIER_DATA : [];
                this.filteredSuppliers = [...this.suppliers]; // 深拷贝避免引用问题
                console.log('供应商数据加载成功:', this.suppliers);
            } catch (error) {
                console.error('数据加载失败:', error);
                this.suppliers = [];
                this.filteredSuppliers = [];
            }
        },
        search() {
            if (!this.searchKeyword || this.searchKeyword.trim() === '') {
                this.filteredSuppliers = this.suppliers;
            } else {
                const keyword = this.searchKeyword.toLowerCase().trim();
                this.filteredSuppliers = this.suppliers.filter(supplier =>
                    supplier.supl_name.toLowerCase().includes(keyword)
                );
            }
        },
        goPage(page) {
            // ✅ 修复：严格边界判断，防止越界
            if (page < 1) page = 1;
            if (page > this.totalPages) page = this.totalPages;
            window.location.href = "?page=" + page;
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

        // 删除供应商（优化版）
        async deleteSupplier(id) {
            if (!confirm("确定要删除该供应商吗？删除后无法恢复！")) {
                return;
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const res = await axios.post(`/supldel/${id}/`, {}, {
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                alert("删除成功！");
                location.reload();
            } catch (err) {
                console.error(err);
                // ✅ 优化：显示真实错误信息
                const msg = err.response?.data?.msg || "删除失败，请检查权限或网络";
                alert(msg);
            }
        }
    }
});