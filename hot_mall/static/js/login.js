let vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法
    delimiters: ['[[', ']]'],
    data: {
        username: '',
        password: '',

        error_username: false,
        error_password: false,
        remembered: false,
    },
    methods: {
        // 检查账号
        check_username(){
        	let re = /^[a-zA-Z0-9_-]{5,20}$/;
			if (re.test(this.username)) {
                this.error_username = false;
            } else {
                this.error_username = true;
            }
        },
        // 登录密码：仅校验非空与合理长度（具体字符由服务端 authenticate；支持含 @、_ 等）
        check_password(){
            const p = this.password != null ? String(this.password) : '';
            if (p.length >= 8 && p.length <= 128) {
                this.error_password = false;
            } else {
                this.error_password = true;
            }
        },
        // 表单提交
        on_submit(e){
            this.check_username();
            this.check_password();

            if (this.error_username == true || this.error_password == true) {
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                return false;
            }
        },
        // qq登录
        qq_login(){
            let next = get_query_string('next') || '/';
            let url = '/qq/login/?next=' + next;
            axios.get(url, {
                responseType: 'json'
            })
                .then(response => {
                    location.href = response.data.login_url;
                })
                .catch(error => {
                    console.log(error.response);
                })
        }
    }
});