// ==================== Vue2 重写版：会员管理 ====================
new Vue({
  el: '#app',  // 挂载到父页面的 #app，完美兼容 base.html
  delimiters: ['[[', ']]'],  // 与 Django 模板语法隔离

  data() {
    return {
      currentPage: 1,
      totalPages: 1,
      keyword: '',
      memberList: [],  // 会员列表（响应式）
      loading: false,
      is_superuser: window.is_superuser,
      newPassword: '',
      resetUserId: null,
      resetModal: null
    }
  },

  mounted() {
    // 页面加载自动请求第一页
    this.loadData(1);

    // 初始化模态框
    this.resetModal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));

    // 回车搜索
    const keywordInput = document.getElementById('keyword');
    if (keywordInput) {
      keywordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.searchMember();
        }
      });
    }
  },

  methods: {
    // 加载数据
    async loadData(page) {
      this.loading = true;
      try {
        const res = await fetch(`/members/api/?page=${page}&keyword=${encodeURIComponent(this.keyword)}`);
        if (!res.ok) throw new Error('请求异常');

        const data = await res.json();
        this.currentPage = data.current_page;
        this.totalPages = data.total_pages;
        this.memberList = data.results;
      } catch (err) {
        console.error('加载失败：', err);
        this.memberList = [];
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
    searchMember() {
      this.keyword = document.getElementById('keyword').value.trim();
      this.loadData(1);
    },

    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return '-';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    // 重置密码
    resetPassword(userId) {
      this.resetUserId = userId;
      this.newPassword = '';
      this.resetModal.show();
    },

    // 确认重置密码
    async confirmResetPassword() {
      if (!this.newPassword) {
        alert('请输入新密码');
        return;
      }

      if (this.newPassword.length < 6) {
        alert('密码长度不能少于6位');
        return;
      }

      try {
        const formData = new FormData();
        formData.append('new_password', this.newPassword);

        const res = await fetch(`/members/reset-password/${this.resetUserId}/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.csrfToken
          },
          body: formData
        });

        const data = await res.json();
        if (data.success) {
          alert(data.message);
          this.resetModal.hide();
        } else {
          alert(data.message);
        }
      } catch (err) {
        console.error('重置密码失败：', err);
        alert('重置密码失败，请重试');
      }
    }
  }
});