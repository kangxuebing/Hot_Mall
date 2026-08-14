// ==================== Vue2 重写版：商品管理 SKU ====================
new Vue({
  el: '#app',  // 挂载到父页面的 #app，完美兼容 base.html
  delimiters: ['[[', ']]'],  // 与 Django 模板语法隔离

  data() {
    return {
      currentPage: 1,
      totalPages: 1,
      keyword: '',
      skuList: [],  // 商品列表（响应式）
      loading: false,
      is_superuser: window.is_superuser
    }
  },

  mounted() {
    // 从顶部搜索框 URL 中获取 q=xxx
    const urlParams = new URLSearchParams(window.location.search);
    this.keyword = urlParams.get('q') || '';

    // 页面加载自动请求第一页
    this.loadData(1);

    // 回车搜索（保留原功能）
    const keywordInput = document.getElementById('keyword');
    keywordInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.searchSKU();
      }
    });
  },

  methods: {
    // 加载数据
    async loadData(page) {
      this.loading = true;
      try {
        const res = await fetch(`/api/skus/?page=${page}&keyword=${encodeURIComponent(this.keyword)}`);
        if (!res.ok) throw new Error('请求异常');

        const data = await res.json();
        this.currentPage = data.current_page;
        this.totalPages = data.total_pages;
        this.skuList = data.results;
      } catch (err) {
        console.error('加载失败：', err);
        this.skuList = [];
      } finally {
        this.loading = false;
      }
    },

    // 上一页
    prevPage() {
      if (this.currentPage > 1) this.loadData(this.currentPage - 1);
    },

    // 下一页
    nextPage() {
      if (this.currentPage < this.totalPages) this.loadData(this.currentPage + 1);
    },

    // 跳页
    goPage(page) {
      this.loadData(page);
    },

    // 最后一页
    lastPage() {
      this.loadData(this.totalPages);
    },

    // 搜索
    searchSKU() {
      this.keyword = document.getElementById('keyword').value.trim();
      this.loadData(1);
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
          this.loadData(this.currentPage);
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