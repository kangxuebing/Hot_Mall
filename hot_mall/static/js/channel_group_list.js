new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            currentPage: 1,
            totalPages: 1
        }
    },
    mounted() {
        this.getPageInfo();
    },
    methods: {
        getPageInfo() {
            // 从URL获取当前页码
            const urlParams = new URLSearchParams(window.location.search);
            this.currentPage = parseInt(urlParams.get('page')) || 1;
            // 从隐藏域读取总页数
            this.totalPages = parseInt(document.getElementById('total_pages').value) || 1;
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

        // 频道组异步删除
        async deleteChannelGroup(id) {
            if (!confirm("确定要删除该频道组吗？删除后无法恢复！")) {
                return;
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const res = await axios.post(`/channel-group/delete/${id}/`, {}, {
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
