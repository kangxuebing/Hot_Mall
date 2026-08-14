new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                name: ''
            },
            errors: {}
        };
    },
    mounted() {
        // 编辑页自动回填数据
        if (typeof CHANNEL_GROUP_DATA !== 'undefined' && CHANNEL_GROUP_DATA) {
            this.form = { ...CHANNEL_GROUP_DATA };
        }
    },
    methods: {
        // 表单校验+提交 同品牌新增逻辑
        submitForm() {
            this.errors = {};
            const f = this.form;
            // 获取输入框真实值
            const groupName = document.querySelector('input[name="name"]').value.trim();

            // 非空必填校验
            if (!groupName) {
                this.errors.name = '频道组名称不能为空';
                return;
            }

            // 二次确认弹窗
            if (!confirm('确定保存频道组信息？')) return;

            // 提交原生表单
            document.getElementById("channelGroupForm").submit();
        }
    }
});