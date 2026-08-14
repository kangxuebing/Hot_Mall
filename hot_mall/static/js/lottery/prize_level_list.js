$(function () {
    // Vue应用实例
    new Vue({
        el: '#app',
        data: {
            csrfToken: '',
            deleteUrl: ''
        },
        methods: {
            deleteLevel: function (levelId, event) {
                if (!confirm('确定要删除这个中奖等级吗？删除后无法恢复！')) {
                    return;
                }
                const $btn = $(event.currentTarget);
                $btn.prop('disabled', true).text('删除中...');

                $.ajax({
                    url: this.deleteUrl,
                    method: "POST",
                    data: {
                        id: levelId,
                        csrfmiddlewaretoken: this.csrfToken
                    },
                    success: function (res) {
                        if (res.code === 0) {
                            alert('删除成功');
                            $(`tr[data-level-id="${levelId}"]`).remove();
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
        mounted: function () {
            // 从模板中获取数据
            const viewData = this.$el.querySelector('[data-view="prize-level-list"]');
            if (viewData) {
                this.csrfToken = viewData.getAttribute('data-csrf-token');
                this.deleteUrl = viewData.getAttribute('data-delete-url');
            }
        }
    });
});
