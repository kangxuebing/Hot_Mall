new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                spec: '',
                value: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页面自动回填数据+下拉选中
        if (typeof SPEC_OPTION_DATA !== 'undefined' && SPEC_OPTION_DATA) {
            this.form = { ...SPEC_OPTION_DATA };
            document.querySelector('select[name="spec"]').value = this.form.spec;
        }
    },
    methods: {
        submitForm() {
            this.errors = {};
            // 获取表单值
            const specVal = document.querySelector('select[name="spec"]').value.trim();
            const optionVal = document.querySelector('input[name="value"]').value.trim();

            // 1. 规格必选校验
            if (!specVal) {
                this.errors.spec = '请选择所属规格';
                return;
            }
            // 2. 选项值非空校验
            if (!optionVal) {
                this.errors.value = '规格选项值不能为空';
                return;
            }

            // 二次确认保存
            if (!confirm('确定保存规格选项信息？')) return;

            // 提交原生表单
            document.getElementById("specOptionForm").submit();
        }
    }
});