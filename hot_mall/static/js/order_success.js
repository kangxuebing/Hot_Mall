let vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        username: getCookie('username'),
    },
    mounted(){
    },
    methods: {
        // 发起支付
        order_payment(){
            let order_id = get_query_string('order_id');
            let url = '/payment/' + order_id + '/';
            axios.get(url, {
                responseType: 'json'
            })
                .then(response => {
                    if (response.data.code == '0') {
                        if (response.data.alipay_url) {
                            location.href = response.data.alipay_url;
                        } else if (response.data.wechat_pay_url) {
                            location.href = response.data.wechat_pay_url;
                        } else {
                            alert('无法获取支付地址');
                        }
                    } else if (response.data.code == '4101') {
                        location.href = '/login/?next=/orders/info/1/';
                    } else {
                        console.log(response.data);
                        alert(response.data.errmsg);
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
    }
});