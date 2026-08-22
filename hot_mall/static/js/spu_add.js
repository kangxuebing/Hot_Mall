new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                name: '',
                brand: '',
                category1: '',
                category2: '',
                category3: '',
                sales: '',
                comments: '',
                desc_detail: '',
                desc_pack: '',
                desc_service: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页面自动回填数据+下拉选中
        if (typeof SPU_DATA !== 'undefined' && SPU_DATA) {
            this.form = { ...SPU_DATA };
            document.querySelector('select[name="brand"]').value = this.form.brand;
            document.querySelector('select[name="category1"]').value = this.form.category1;
            document.querySelector('select[name="category2"]').value = this.form.category2;
            document.querySelector('select[name="category3"]').value = this.form.category3;
        }
    },
    methods: {
        submitForm() {
            this.errors = {};
            // 获取表单值
            const name = document.querySelector('input[name="name"]').value.trim();
            const brand = document.querySelector('select[name="brand"]').value.trim();
            const c1 = document.querySelector('select[name="category1"]').value.trim();
            const c2 = document.querySelector('select[name="category2"]').value.trim();
            const c3 = document.querySelector('select[name="category3"]').value.trim();
            const sales = document.querySelector('input[name="sales"]').value.trim();
            const comments = document.querySelector('input[name="comments"]').value.trim();

            console.log('表单数据:', { name, brand, c1, c2, c3, sales, comments });

            // 1. 商品名称非空校验
            if (!name) {
                this.errors.name = '商品名称不能为空';
                return;
            }
            // 2. 品牌必选
            if (!brand) {
                this.errors.brand = '请选择所属品牌';
                return;
            }
            // 3. 一级分类必选
            if (!c1) {
                this.errors.category1 = '请选择一级商品类别';
                return;
            }
            // 4. 销量非负整数校验
            if (sales && (!/^\d+$/.test(sales) || parseInt(sales) < 0)) {
                this.errors.sales = '销量必须为非负整数';
                return;
            }
            // 5. 评价数非负整数校验
            if (comments && (!/^\d+$/.test(comments) || parseInt(comments) < 0)) {
                this.errors.comments = '评价数必须为非负整数';
                return;
            }

            // 处理空值 - 如果二级或三级类别未选择，设置为空字符串而不是'请选择'
            if (c2 === '' || c2 === '请选择') {
                document.querySelector('select[name="category2"]').value = '';
            }
            if (c3 === '' || c3 === '请选择') {
                document.querySelector('select[name="category3"]').value = '';
            }

            // 二次确认保存
            if (!confirm('确定保存SPU商品信息？')) return;

            console.log('准备提交表单...');
            const form = document.getElementById("spuForm");
            console.log('表单元素:', form);
            console.log('表单action:', form.action);
            console.log('表单method:', form.method);

            // 提交原生表单
            try {
                form.submit();
                console.log('表单提交成功');
            } catch (e) {
                console.error('表单提交失败:', e);
                alert('表单提交失败: ' + e.message);
            }
        }
    }
});