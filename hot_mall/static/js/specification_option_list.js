new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            currentPage: 1,
            totalPages: 1,
            options: [],
            filteredOptions: [],
            searchSpec: '',
            searchValue: ''
        }
    },
    mounted() {
        this.getPageInfo();
        this.loadData();
    },
    methods: {
        getPageInfo() {
            // 从URL获取当前页码
            const urlParams = new URLSearchParams(window.location.search);
            this.currentPage = parseInt(urlParams.get('page')) || 1;
            // 从隐藏域读取总页数
            this.totalPages = parseInt(document.getElementById('total_pages').value) || 1;
        },
        loadData() {
            this.options = window.SPEC_OPTION_DATA || [];
            this.filteredOptions = this.options;
        },
        search() {
            this.filteredOptions = this.options.filter(option => {
                let matchSpec = true;
                let matchValue = true;

                if (this.searchSpec && this.searchSpec.trim() !== '') {
                    matchSpec = option.spec_name.toLowerCase().includes(this.searchSpec.toLowerCase().trim());
                }

                if (this.searchValue && this.searchValue.trim() !== '') {
                    matchValue = option.value.toLowerCase().includes(this.searchValue.toLowerCase().trim());
                }

                return matchSpec && matchValue;
            });
        },
        goPage(page) {
            // 边界防越界
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

        // 规格选项异步删除
        async deleteSpecOption(id) {
            if (!confirm("确定要删除该规格选项吗？删除后无法恢复！")) {
                return;
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const res = await axios.post(`/spec-option/delete/${id}/`, {}, {
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                alert("删除成功！");
                location.reload();
            } catch (err) {
                console.error(err);
                const msg = err.response?.data?.msg || "删除失败，请检查权限或网络";
                alert(msg);
            }
        }
    }
});
