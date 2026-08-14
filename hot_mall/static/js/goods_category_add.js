new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                name: '',
                parent: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页面自动回填表单+下拉选中
        if (typeof CATEGORY_DATA !== 'undefined' && CATEGORY_DATA) {
            this.form = { ...CATEGORY_DATA };
            document.querySelector('select[name="parent"]').value = this.form.parent;
        }
    },
    methods: {
        submitForm() {
            this.errors = {};
            // 获取表单输入值
            const cateName = document.querySelector('input[name="name"]').value.trim();

            // 类别名称必填校验
            if (!cateName) {
                this.errors.name = '商品类别名称不能为空';
                return;
            }

            // 二次确认弹窗
            if (!confirm('确定保存商品类别信息？')) return;

            // 提交原生表单
            document.getElementById("categoryForm").submit();
        }
    }
});