new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            currentPage: 1,
            totalPages: 1,
            specs: [],
            filteredSpecs: [],
            searchKeyword: ''
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
            this.specs = window.SPU_SPEC_DATA || [];
            this.filteredSpecs = this.specs;
        },
        search() {
            if (!this.searchKeyword || this.searchKeyword.trim() === '') {
                this.filteredSpecs = this.specs;
            } else {
                const keyword = this.searchKeyword.toLowerCase().trim();
                this.filteredSpecs = this.specs.filter(spec =>
                    spec.spu_name.toLowerCase().includes(keyword)
                );
            }
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

        // SPU规格异步删除
        async deleteSpuSpec(id) {
            if (!confirm("确定要删除该SPU规格吗？删除后无法恢复！")) {
                return;
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const res = await axios.post(`/spu-spec/delete/${id}/`, {}, {
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
