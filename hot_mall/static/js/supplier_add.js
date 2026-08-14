new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data() {
        return {
            form: {
                supl_name: '',
                supl_addr: '',
                supl_phone: '',
                wechat: '',
                business_license: '',
                level: ''
            },
            errors: {},
            selectedImageId: null,
            selectedSupplierId: null
        };
    },
    mounted() {
        // 初始化表单数据
        if (typeof SUPPLIER_DATA !== 'undefined') {
            this.form = { ...SUPPLIER_DATA };
        }
        this.bindPreviewEvents();
        this.bindBtnEvents();
        this.selectInitialImage();
    },
    methods: {
        // 表单验证提交
        submitForm() {
            this.errors = {};
            const f = this.form;
            if (!f.supl_name.trim()) {
                this.errors.supl_name = '供应商名称不能为空';
                return;
            }
            if (!confirm('确定保存？')) return;
            document.getElementById("supplierForm").submit();
        },

        // 绑定图片点击事件（和sku完全一致）
        bindPreviewEvents() {
            const items = document.querySelectorAll('[data-preview-item]');
            items.forEach(item => {
                item.addEventListener('click', () => this.selectImage(item));
            });
        },

        // 绑定按钮事件（和sku完全一致）
        bindBtnEvents() {
            const delBtn = document.getElementById('selected-delete-btn');
            delBtn.addEventListener('click', () => this.deleteImage());
            const defaultBtn = document.getElementById('selected-set-default-btn');
            defaultBtn.addEventListener('click', () => this.setDefaultImage());
        },

        // 默认选中第一张（和sku完全一致）
        selectInitialImage() {
            const first = document.querySelector('[data-preview-item]');
            if (first) this.selectImage(first);
        },

        // 选择图片（和sku完全一致结构）
        selectImage(item) {
            document.querySelectorAll('[data-preview-item]').forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            this.selectedImageId = item.dataset.imageId;
            this.selectedSupplierId = item.dataset.supplierId;

            const url = item.dataset.imageUrl;
            const name = item.dataset.imageName || '供应商图片';
            const isDefault = item.dataset.isDefault;

            document.getElementById('selected-image-preview').src = url;
            document.getElementById('selected-image-name').textContent = name;
            document.getElementById('selected-image-status').textContent = isDefault === '1' ? '默认图片' : '普通图片';
        },

        // 设置默认图片（async/await 风格和sku完全一致）
        async setDefaultImage() {
            const supplierId = this.selectedSupplierId;
            const imageId = this.selectedImageId;

            if (!supplierId || !imageId) {
                alert('请先选择图片');
                return;
            }
            if (!confirm('确定将这张图片设为默认？')) return;

            try {
                const res = await fetch(`/setsupldefimage/${supplierId}/${imageId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                const data = await res.json();
                if (data.status === 'success') {
                    alert('设置成功！');
                    location.reload();
                } else {
                    alert('设置失败：' + (data.message || '服务器错误'));
                }
            } catch (e) {
                console.error(e);
                alert('设置失败');
            }
        },

        // 删除图片（async/await 风格和sku完全一致）
        async deleteImage() {
            const id = this.selectedImageId;
            if (!id) {
                alert('请先选择图片');
                return;
            }
            if (!confirm('确定删除这张图片？')) return;

            try {
                const res = await fetch(`/delsuplimage/${id}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await res.json();
                if (data.status === 'success') {
                    // 删除DOM元素
                    document.querySelector('[data-image-id="' + id + '"]')?.remove();

                    // 重新选择第一张
                    const remaining = document.querySelectorAll('[data-preview-item]');
                    if (remaining.length) {
                        this.selectImage(remaining[0]);
                    } else {
                        document.getElementById('selected-image-preview').src = '';
                        document.getElementById('selected-image-name').textContent = '-';
                        document.getElementById('selected-image-status').textContent = '-';
                    }
                    alert('删除成功');
                } else {
                    alert('删除失败：' + data.message);
                }
            } catch (e) {
                console.error(e);
                alert('删除失败');
            }
        }
    }
});