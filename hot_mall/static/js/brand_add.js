new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                name: '',
                first_letter: ''
            },
            errors: {},
            // Logo图片校验配置
            logoFile: null,
            maxImgSize: 5 * 1024 * 1024, // 最大5MB
            minWidth: 80,                // 最小宽度
            minHeight: 80,               // 最小高度
            maxWidth: 800,               // 最大宽度
            maxHeight: 800               // 最大高度
        };
    },
    mounted() {
        // 编辑页回填表单数据
        if (typeof BRAND_DATA !== 'undefined') {
            this.form = { ...BRAND_DATA };
        }
    },
    methods: {
        // 监听Logo图片选择，校验大小+尺寸
        handleLogoChange(e) {
            const file = e.target.files[0];
            if (!file) {
                this.logoFile = null;
                return;
            }
            this.logoFile = file;

            // 1. 校验图片大小
            if (file.size > this.maxImgSize) {
                alert('Logo图片不能超过5MB！');
                e.target.value = '';
                this.logoFile = null;
                return;
            }

            // 2. 校验图片宽高尺寸
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = (res) => {
                const img = new Image();
                img.src = res.target.result;
                img.onload = () => {
                    const w = img.width;
                    const h = img.height;
                    if (w < this.minWidth || h < this.minHeight) {
                        alert(`图片尺寸过小，最小尺寸${this.minWidth}*${this.minHeight}像素`);
                        e.target.value = '';
                        this.logoFile = null;
                        return;
                    }
                    if (w > this.maxWidth || h > this.maxHeight) {
                        alert(`图片尺寸过大，最大尺寸${this.maxWidth}*${this.maxHeight}像素`);
                        e.target.value = '';
                        this.logoFile = null;
                        return;
                    }
                };
            };
        },

        // 表单统一提交校验
        submitForm() {
            this.errors = {};
            const f = this.form;

            // 1. 品牌名称非空校验
            if (!f.name.trim()) {
                this.errors.name = '品牌名称不能为空';
                return;
            }

            // 2. 首字母格式校验：仅支持单个大小写英文字母
            const letterReg = /^[A-Za-z]$/;
            if (f.first_letter && !letterReg.test(f.first_letter.trim())) {
                this.errors.first_letter = '首字母只能填写单个英文字母';
                return;
            }

            // 3. 二次确认保存
            if (!confirm('确定保存品牌信息？')) return;

            // 提交原生表单
            document.getElementById("brandForm").submit();
        }
    }
});