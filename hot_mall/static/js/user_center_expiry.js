// user_center_expiry.js 临近保质期商品专用脚本
// 合并所有原有Vue逻辑 + 数据校验方法，移除冲突重复函数

// Vue实例初始化
let vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        currentPage: window.pageNum,
        totalPages: window.totalPage,
        skuList: [],
        filteredSkuList: [],
        searchKeyword: '',
        loading: false,
        is_superuser: window.isSuperUser
    },
    mounted(){
        this.loadData();
    },
    methods: {
        // 加载初始化商品数据
        loadData() {
            this.skuList = window.initSkuData;
            this.filteredSkuList = this.skuList;
            this.loading = false;
        },

        // 搜索功能
        search() {
            if (!this.searchKeyword || this.searchKeyword.trim() === '') {
                this.filteredSkuList = this.skuList;
                return;
            }
            const keyword = this.searchKeyword.toLowerCase().trim();
            this.filteredSkuList = this.skuList.filter(sku =>
                sku.name.toLowerCase().includes(keyword)
            );
        },

        // 上一页
        prevPage() {
            if (this.currentPage > 1) {
                window.location.href = '/expirysku/?page=' + (this.currentPage - 1);
            }
        },

        // 下一页
        nextPage() {
            if (this.currentPage < this.totalPages) {
                window.location.href = '/expirysku/?page=' + (this.currentPage + 1);
            }
        },

        // 跳页
        goPage(page) {
            window.location.href = '/expirysku/?page=' + page;
        },

        // 最后一页
        lastPage() {
            window.location.href = '/expirysku/?page=' + this.totalPages;
        },

        // 删除商品
        async deleteSKU(id) {
            if (!confirm('确定要删除该商品吗？')) return;
            try {
                const res = await fetch(`/delsku/${id}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken,
                        'Content-Type': 'application/json'
                    }
                });
                if (res.ok) {
                    location.reload();
                } else {
                    alert('删除失败');
                }
            } catch (err) {
                console.error('删除失败：', err);
                alert('删除失败，请重试');
            }
        }
    }
});

// 列表数据自动校验全局方法
function validateGoodsData(sku) {
    // 1. 价格/库存非空校验
    if (!sku.price || !sku.cost_price || !sku.market_price || !sku.stock) {
        alert(`商品【${sku.name}】存在空值，请完善价格/库存信息！`);
        return false;
    }
    // 2. 数字校验
    if (isNaN(sku.price) || isNaN(sku.cost_price) || isNaN(sku.market_price) || isNaN(sku.stock)) {
        alert(`商品【${sku.name}】价格/库存必须是数字！`);
        return false;
    }
    // 3. 负数拦截
    if (sku.price < 0 || sku.cost_price < 0 || sku.market_price < 0 || sku.stock < 0 || sku.sales < 0 || sku.shelf_life < 0 || sku.comments < 0) {
        alert(`商品【${sku.name}】价格/库存/销量/保质期/评论数不能为负数！`);
        return false;
    }
    // 4. 进价大于售价提醒
    if (Number(sku.cost_price) > Number(sku.price)) {
        if (!confirm(`商品【${sku.name}】进价大于售价，是否继续？`)) {
            return false;
        }
    }
    return true;
}