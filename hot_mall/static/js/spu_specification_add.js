new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                spu: '',
                name: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页面自动回填数据并选中下拉
        if (typeof SPU_SPEC_DATA !== 'undefined' && SPU_SPEC_DATA) {
            this.form = { ...SPU_SPEC_DATA };
            document.querySelector('select[name="spu"]').value = this.form.spu;
        }
    },
    methods: {
        submitForm() {
            this.errors = {};
            // 获取表单值
            const spuVal = document.querySelector('select[name="spu"]').value.trim();
            const specName = document.querySelector('input[name="name"]').value.trim();

            // 前端表单校验
            if (!spuVal) {
                this.errors.spu = '请选择所属SPU商品';
                return;
            }
            if (!specName) {
                this.errors.name = '规格名称不能为空';
                return;
            }

            // 二次确认
            if (!confirm('确定保存SPU规格信息？')) return;

            // 提交原生表单
            document.getElementById("spuSpecForm").submit();
        }
    }
});