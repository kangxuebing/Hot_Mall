let vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        username: getCookie('username'),
        old_password: '',
        new_password: '',
        new_password2: '',
        error_old_password: false,
        error_new_password: false,
        error_new_password2: false,

        error_new_password_message: '',
        error_new_password2_message: '',
    },
    methods: {
        // 检查旧密码（仅校验已填写，格式由服务端 check_password 校验）
        check_old_password(){
            if (this.old_password && String(this.old_password).length > 0) {
                this.error_old_password = false;
            } else {
                this.error_old_password = true;
            }
        },
        // 检查新密码（与注册页 register.js 规则一致）
        check_new_password(){
            if (!this.new_password || !String(this.new_password).trim()) {
                this.error_new_password = true;
                this.error_new_password_message = '请填写新密码';
                return;
            }
            if (this.old_password === this.new_password) {
                this.error_new_password = true;
                this.error_new_password_message = '新密码不能和旧密码一致';
                return;
            }
            // 与 users.constants.USER_PASSWORD_REGEX 一致：含数字/小写/大写/特殊字符，仅可打印 ASCII
            let re = /^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9\s])[\x21-\x7E]{8,20}$/;
            if (!re.test(this.new_password)) {
                this.error_new_password = true;
                this.error_new_password_message = '密码须为8-20位可打印字符，且含数字、小写、大写及特殊符号（如@、_）';
                return;
            }
            this.error_new_password = false;
            this.error_new_password_message = '';
            // 新密码合法后，若已填写确认密码则联动校验
            if (this.new_password2 && String(this.new_password2).length > 0) {
                this.check_new_password2();
            }
        },
        // 检查确认新密码：先必填，再与新密码逐字符一致
        check_new_password2(){
            const p2 = this.new_password2 != null ? String(this.new_password2) : '';
            if (!p2.trim()) {
                this.error_new_password2 = true;
                this.error_new_password2_message = '请填写确认新密码';
                return;
            }
            if (this.new_password !== this.new_password2) {
                this.error_new_password2 = true;
                this.error_new_password2_message = '两次输入的新密码不一致';
                return;
            }
            this.error_new_password2 = false;
            this.error_new_password2_message = '';
        },
        // 提交修改密码：始终先拦截 submit，校验通过后使用原生 form.submit() 发起 POST（避免 window.event 无效导致无法阻止提交）
        on_submit(){
            this.check_old_password();
            this.check_new_password();
            this.check_new_password2();

            if (this.error_old_password || this.error_new_password || this.error_new_password2) {
                return;
            }
            const form = this.$refs.pwdForm;
            if (form && typeof form.submit === 'function') {
                form.submit();
            }
        },
    }
});