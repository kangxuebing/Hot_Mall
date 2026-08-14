$(function () {
    // 使用base.html中的统一#app容器
    const app = document.getElementById('app');
    if (!app) return;
    
    // 检查是否是奖品列表页面
    const viewData = app.querySelector('[data-view="prize-list"]');
    if (!viewData) return;
    
    // Vue应用实例
    new Vue({
        el: '#app',
        data: {
            csrfToken: '',
            deleteUrl: ''
        },
        methods: {
            deletePrize: function(prizeId, event) {
                if (!confirm('确定要删除这个奖品吗？删除后无法恢复！')) {
                    return;
                }
                
                const $btn = $(event.currentTarget);
                $btn.prop('disabled', true).text('删除中...');

                $.ajax({
                    url: this.deleteUrl,
                    method: "POST",
                    data: {
                        id: prizeId,
                        csrfmiddlewaretoken: this.csrfToken
                    },
                    success: function (res) {
                        if (res.code === 0) {
                            alert('删除成功');
                            $(`tr[data-prize-id="${prizeId}"]`).remove();
                        } else {
                            alert(res.msg || '删除失败');
                            $btn.prop('disabled', false).text('删除');
                        }
                    },
                    error: function () {
                        alert('网络异常，请重试');
                        $btn.prop('disabled', false).text('删除');
                    }
                });
            }
        },
        mounted: function() {
            // 从模板中获取数据
            const viewData = this.$el.querySelector('[data-view="prize-list"]');
            if (viewData) {
                this.csrfToken = viewData.getAttribute('data-csrf-token');
                this.deleteUrl = viewData.getAttribute('data-delete-url');
            }
        }
    });
});
