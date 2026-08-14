new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            currentPage: 1,
            totalPages: 1,
            contents: [],
            filteredContents: [],
            searchCategory: '',
            searchTitle: ''
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
            this.contents = window.CONTENT_DATA || [];
            this.filteredContents = this.contents;
        },
        search() {
            this.filteredContents = this.contents.filter(content => {
                let matchCategory = true;
                let matchTitle = true;

                if (this.searchCategory && this.searchCategory.trim() !== '') {
                    matchCategory = content.category_name.toLowerCase().includes(this.searchCategory.toLowerCase().trim());
                }

                if (this.searchTitle && this.searchTitle.trim() !== '') {
                    matchTitle = content.title.toLowerCase().includes(this.searchTitle.toLowerCase().trim());
                }

                return matchCategory && matchTitle;
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

        // 广告内容异步删除
        async deleteContent(id) {
            if (!confirm("确定要删除该广告内容吗？删除后无法恢复！")) {
                return;
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const res = await axios.post(`/content/delete/${id}/`, {}, {
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
