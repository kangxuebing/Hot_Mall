// 促销商品表单页面JavaScript - Vue.js版本
new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        discountType: '1',
        skuId: '',
        discountRate: '0.90',
        discountAmount: '0',
        startTime: '',
        endTime: '',
        isActive: true,
        description: '',
        showDiscountRate: true,
        showDiscountAmount: false
    },
    methods: {
        toggleDiscountFields: function() {
            if (this.discountType === '1') {
                this.showDiscountRate = true;
                this.showDiscountAmount = false;
            } else {
                this.showDiscountRate = false;
                this.showDiscountAmount = true;
            }
        },
        
        validateForm: function() {
            // 验证商品必选
            if (!this.skuId) {
                alert('请选择商品！');
                return false;
            }

            // 验证时间不为空
            if (!this.startTime || !this.endTime) {
                alert('请设置促销开始、结束时间！');
                return false;
            }

            // 转为数字再校验
            const discountRate = Number(this.discountRate);
            const discountAmount = Number(this.discountAmount);

            // 校验折扣
            if (this.discountType === '1') {
                if (!this.discountRate || isNaN(discountRate) || discountRate < 0.01 || discountRate > 1.00) {
                    alert('折扣率必须在0.01‑1.00之间！例如0.9代表9折');
                    return false;
                }
            } else {
                if (!this.discountAmount || isNaN(discountAmount) || discountAmount <= 0) {
                    alert('优惠金额必须大于0！');
                    return false;
                }
            }

            // 校验时间逻辑：结束必须晚于开始
            if (new Date(this.startTime) >= new Date(this.endTime)) {
                alert('结束时间必须大于开始时间！');
                return false;
            }

            return true;
        },
        
        submitForm: function() {
            if (this.validateForm()) {
                document.getElementById('promotionForm').submit();
            }
        }
    },
    mounted: function() {
        // 页面初始化时设置折扣类型
        const discountTypeSelect = document.querySelector('[name="discount_type"]');
        if (discountTypeSelect) {
            this.discountType = discountTypeSelect.value;
            this.toggleDiscountFields();
        }
        
        // 监听折扣类型变化
        if (discountTypeSelect) {
            discountTypeSelect.addEventListener('change', (e) => {
                this.discountType = e.target.value;
                this.toggleDiscountFields();
            });
        }
    }
});