new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                group: '',
                category: '',
                url: '',
                sequence: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页面回填数据
        if (typeof CHANNEL_DATA !== 'undefined' && CHANNEL_DATA) {
            this.form = { ...CHANNEL_DATA };
            document.querySelector('select[name="group"]').value = this.form.group;
            document.querySelector('select[name="category"]').value = this.form.category;
        }
    },
    methods: {
        // 表单统一校验提交
        submitForm() {
            this.errors = {};
            const f = this.form;

            // 1. 校验频道组
            let groupVal = document.querySelector('select[name="group"]').value.trim();
            if (!groupVal) {
                this.errors.group = '请选择频道组';
                return;
            }

            // 2. 校验类别
            let catVal = document.querySelector('select[name="category"]').value.trim();
            if (!catVal) {
                this.errors.category = '请选择所属类别';
                return;
            }

            // 3. 校验URL
            let urlVal = document.querySelector('input[name="url"]').value.trim();
            if (!urlVal) {
                this.errors.url = 'URL地址不能为空';
                return;
            }
            // 简单URL格式校验
            const urlReg = /^\/[\w\/]*$/;
            if (!urlReg.test(urlVal)) {
                this.errors.url = '请填写合法站内URL';
                return;
            }

            // 4. 校验排序数字
            let seqVal = document.querySelector('input[name="sequence"]').value.trim();
            if (!seqVal) {
                this.errors.sequence = '排序序号不能为空';
                return;
            }
            const seqReg = /^[1-9]\d*$/;
            if (!seqReg.test(seqVal)) {
                this.errors.sequence = '排序必须为正整数';
                return;
            }

            // 二次确认
            if (!confirm('确定保存频道信息？')) return;

            // 提交原生表单
            document.getElementById("channelForm").submit();
        }
    }
});