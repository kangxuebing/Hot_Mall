new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                name: '',
                key: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页自动回填表单数据
        if (typeof CONTENT_CATE_DATA !== 'undefined' && CONTENT_CATE_DATA) {
            this.form = { ...CONTENT_CATE_DATA };
        }
    },
    methods: {
        submitForm() {
            this.errors = {};
            // 获取输入值
            const cateName = document.querySelector('input[name="name"]').value.trim();
            const cateKey = document.querySelector('input[name="key"]').value.trim();

            // 前端非空校验
            if (!cateName) {
                this.errors.name = '内容类别名称不能为空';
                return;
            }
            if (!cateKey) {
                this.errors.key = '类别键名不能为空';
                return;
            }

            // 二次确认保存
            if (!confirm('确定保存内容类别信息？')) return;

            // 提交原生表单
            document.getElementById("contentCategoryForm").submit();
        }
    }
});