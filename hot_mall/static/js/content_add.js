new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                category: '',
                title: '',
                url: '',
                sequence: '',
                status: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页自动回填下拉与表单值
        if (typeof CONTENT_DATA !== 'undefined' && CONTENT_DATA) {
            this.form = { ...CONTENT_DATA };
            document.querySelector('select[name="category"]').value = this.form.category;
            document.querySelector('select[name="status"]').value = this.form.status;
        }
    },
    methods: {
        submitForm() {
            this.errors = {};
            // 获取表单值
            const cateVal = document.querySelector('select[name="category"]').value.trim();
            const titleVal = document.querySelector('input[name="title"]').value.trim();
            const urlVal = document.querySelector('input[name="url"]').value.trim();
            const seqVal = document.querySelector('input[name="sequence"]').value.trim();

            // 1. 内容类别必选
            if (!cateVal) {
                this.errors.category = '请选择内容所属类别';
                return;
            }
            // 2. 标题非空
            if (!titleVal) {
                this.errors.title = '内容标题不能为空';
                return;
            }
            // 3. URL非空+简单格式校验
            if (!urlVal) {
                this.errors.url = '跳转URL不能为空';
                return;
            }
            const urlReg = /^\/[\w\/]*$/;
            if (!urlReg.test(urlVal)) {
                this.errors.url = '请填写合法站内URL路径';
                return;
            }
            // 4. 排序正整数校验
            if (!seqVal) {
                this.errors.sequence = '排序序号不能为空';
                return;
            }
            const numReg = /^[1-9]\d*$/;
            if (!numReg.test(seqVal)) {
                this.errors.sequence = '排序必须为正整数';
                return;
            }

            // 二次确认保存
            if (!confirm('确定保存内容信息？')) return;

            // 提交带文件表单
            document.getElementById("contentForm").submit();
        }
    }
});