new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                sku: '',
                spec: '',
                option: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页面自动回填并选中下拉项
        if (typeof SKU_SPEC_DATA !== 'undefined' && SKU_SPEC_DATA) {
            this.form = { ...SKU_SPEC_DATA };
            document.querySelector('select[name="sku"]').value = this.form.sku;
            document.querySelector('select[name="spec"]').value = this.form.spec;
            document.querySelector('select[name="option"]').value = this.form.option;
        }
    },
    methods: {
        submitForm() {
            this.errors = {};
            // 获取所有下拉选中值
            const skuVal = document.querySelector('select[name="sku"]').value.trim();
            const specVal = document.querySelector('select[name="spec"]').value.trim();
            const optVal = document.querySelector('select[name="option"]').value.trim();

            // 表单逐项校验
            if (!skuVal) {
                this.errors.sku = '请选择对应SKU商品';
                return;
            }
            if (!specVal) {
                this.errors.spec = '请选择所属规格';
                return;
            }
            if (!optVal) {
                this.errors.option = '请选择规格选项值';
                return;
            }

            // 二次确认提交
            if (!confirm('确定保存SKU规格关联信息？')) return;

            // 提交原生表单
            document.getElementById("skuSpecForm").submit();
        }
    }
});