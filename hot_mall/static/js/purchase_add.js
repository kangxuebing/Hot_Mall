console.log('Vue 正在初始化...');
const app = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                supplier: '',
                product_name: '',
                product_spec: '',
                barcode: '',
                production_date: '',
                shelf_life: '',
                expiration_date: '',
                purchase_num: '',
                qualified_num: '',
                near_expiry_num: '',
                damaged_num: '',
                purchase_price: '',
                total_price: '',
                purchase_time: '',
                operator: '',
                remark: ''
            },
            errors: {},
            skuSearchMessage: '',
            searchTimeout: null
        };
    },
    mounted() {
        if (typeof PURCHASE_DATA !== 'undefined') {
            const d = { ...PURCHASE_DATA };
            if (d.supplier !== undefined && d.supplier !== null) {
                d.supplier = String(d.supplier);
            }
            this.form = { ...this.form, ...d };
            // 初始化时计算总金额
            this.calculateTotal();
        }
    },
    watch: {
        'form.purchase_num'() {
            this.calculateTotal();
        },
        'form.purchase_price'() {
            this.calculateTotal();
        }
    },
    methods: {
        calculateTotal() {
            const num = parseFloat(this.form.purchase_num);
            const price = parseFloat(this.form.purchase_price);
            if (!isNaN(num) && !isNaN(price) && num > 0 && price >= 0) {
                this.form.total_price = (num * price).toFixed(2);
            }
        },
        searchSKUByBarcode() {
            const barcode = this.form.barcode.trim();
            console.log('开始搜索条码:', barcode);
            
            if (!barcode) {
                this.skuSearchMessage = '';
                return;
            }

            this.skuSearchMessage = '正在搜索...';

            const headers = {
                'X-Requested-With': 'XMLHttpRequest',
            };
            
            // Add CSRF token if available
            if (typeof window.csrfToken !== 'undefined') {
                headers['X-CSRFToken'] = window.csrfToken;
            }

            const url = `/search-sku/?barcode=${encodeURIComponent(barcode)}`;
            console.log('请求URL:', url);
            console.log('当前页面URL:', window.location.href);
            console.log('form.barcode:', this.form.barcode);

            fetch(url, {
                method: 'GET',
                headers: headers,
                credentials: 'same-origin'
            })
                .then(response => {
                    console.log('响应状态:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('响应数据:', data);
                    if (data.success) {
                        // 自动填充商品名称、条码和规格
                        this.$set(this.form, 'product_name', data.sku.name);
                        this.$set(this.form, 'barcode', data.sku.barcode);
                        
                        // 自动填充规格（如果有副标题）
                        if (data.sku.caption) {
                            this.$set(this.form, 'product_spec', data.sku.caption);
                        }
                        
                        console.log('填充后的表单数据:', this.form);
                        this.skuSearchMessage = '✅ 已自动填充商品名称、条码和规格';
                    } else {
                        // 未找到SKU，保留条码，需要手动输入商品名称
                        console.log('未找到SKU:', data.message);
                        this.skuSearchMessage = '⚠️ 未找到该条码的商品，请手动输入商品名称';
                    }
                })
                .catch(error => {
                    console.error('搜索失败:', error);
                    this.skuSearchMessage = '❌ 搜索失败，请检查网络连接';
                });
        },
        searchSKUByName(forceSearch = false) {
            const productName = this.form.product_name.trim();
            if (!productName || productName.length < 2) {
                return;
            }

            // 如果是手动点击搜索，立即执行
            if (forceSearch) {
                this.performNameSearch(productName);
                return;
            }

            // 防抖处理，避免频繁请求
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }

            this.searchTimeout = setTimeout(() => {
                this.performNameSearch(productName);
            }, 500); // 500ms 防抖
        },
        performNameSearch(productName) {
            const headers = {
                'X-Requested-With': 'XMLHttpRequest',
            };
            
            // Add CSRF token if available
            if (typeof window.csrfToken !== 'undefined') {
                headers['X-CSRFToken'] = window.csrfToken;
            }

            fetch(`/search-sku-by-name/?name=${encodeURIComponent(productName)}`, {
                method: 'GET',
                headers: headers,
                credentials: 'same-origin'
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.sku) {
                        // 如果找到了精确匹配，自动填充条码和规格
                        this.form.barcode = data.sku.barcode;
                        
                        if (data.sku.caption) {
                            this.form.product_spec = data.sku.caption;
                        }
                        
                        this.skuSearchMessage = '✅ 已找到匹配商品，自动填充条码和规格';
                    }
                })
                .catch(error => {
                    console.error('按名称搜索失败:', error);
                });
        },
        submitForm() {
            this.errors = {};
            const f = this.form;

            if (!f.supplier) {
                this.errors.supplier = '请选择供应商';
                return;
            }
            if (!f.product_name || !String(f.product_name).trim()) {
                this.errors.product_name = '商品名称不能为空';
                return;
            }
            if (String(f.product_name).length > 200) {
                this.errors.product_name = '不能超过200个字符';
                return;
            }
            if (f.product_spec && String(f.product_spec).length > 200) {
                this.errors.product_spec = '规格不能超过200个字符';
                return;
            }

            const num = parseInt(f.purchase_num, 10);
            if (!f.purchase_num || isNaN(num) || num < 1) {
                this.errors.purchase_num = '进货数量须为不小于1的整数';
                return;
            }

            // 验证数量字段
            const qualifiedNum = parseInt(f.qualified_num, 10);
            if (f.qualified_num && (isNaN(qualifiedNum) || qualifiedNum < 0)) {
                this.errors.qualified_num = '合格数量必须为非负整数';
                return;
            }

            const nearExpiryNum = parseInt(f.near_expiry_num, 10);
            if (f.near_expiry_num && (isNaN(nearExpiryNum) || nearExpiryNum < 0)) {
                this.errors.near_expiry_num = '临保质期数量必须为非负整数';
                return;
            }

            const damagedNum = parseInt(f.damaged_num, 10);
            if (f.damaged_num && (isNaN(damagedNum) || damagedNum < 0)) {
                this.errors.damaged_num = '破损数量必须为非负整数';
                return;
            }

            // 验证总数量不超过进货数量
            const totalQualityNum = (qualifiedNum || 0) + (nearExpiryNum || 0) + (damagedNum || 0);
            if (totalQualityNum > num) {
                this.errors.purchase_num = '合格+临保质期+破损数量不能超过进货数量';
                return;
            }

            const price = parseFloat(f.purchase_price);
            if (f.purchase_price === '' || f.purchase_price === null || isNaN(price) || price < 0) {
                this.errors.purchase_price = '请输入有效的进货单价';
                return;
            }

            const total = parseFloat(f.total_price);
            if (f.total_price === '' || f.total_price === null || isNaN(total) || total < 0) {
                this.errors.total_price = '请输入有效的总金额';
                return;
            }

            if (!f.purchase_time) {
                this.errors.purchase_time = '请选择进货时间';
                return;
            }

            if (f.operator && String(f.operator).length > 50) {
                this.errors.operator = '操作人不能超过50个字符';
                return;
            }

            if (!confirm('确定要保存吗？')) return;
            document.getElementById('purchaseForm').submit();
        }
    }
});
