new Vue({
    el: '#app',
    data() {
        return {
            selectedImageId: null,
            selectedSkuId: null
        }
    },
    mounted() {
        this.bindPreviewEvents();
        this.bindBtnEvents();
        this.selectInitialImage();
    },
    methods: {
        bindPreviewEvents() {
            const items = document.querySelectorAll('[data-preview-item]');
            items.forEach(item => {
                item.addEventListener('click', () => this.selectImage(item));
            });
        },
        bindBtnEvents() {
            const delBtn = document.getElementById('selected-delete-btn');
            delBtn.addEventListener('click', () => this.deleteImage());
            const defaultBtn = document.getElementById('selected-set-default-btn');
            defaultBtn.addEventListener('click', () => this.setDefaultImage());
        },
        selectInitialImage() {
            const first = document.querySelector('[data-preview-item]');
            if (first) this.selectImage(first);
        },
        selectImage(item) {
            document.querySelectorAll('[data-preview-item]').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            this.selectedImageId = item.dataset.imageId;
            this.selectedSkuId = item.dataset.skuId;
            const url = item.dataset.imageUrl;
            const name = item.dataset.imageName;
            const isDefault = item.dataset.isDefault;
            document.getElementById('selected-image-preview').src = url;
            document.getElementById('selected-image-name').textContent = name;
            document.getElementById('selected-image-status').textContent = isDefault === '1' ? '默认图片' : '普通图片';
        },
        async setDefaultImage() {
            const skuId = this.selectedSkuId;
            const imageId = this.selectedImageId;
            if (!skuId || !imageId) {
                alert('请先选择图片');
                return;
            }
            if (!confirm('确定将这张图片设为默认？')) return;

            try {
                const res = await fetch(`/setdefimage/${skuId}/${imageId}/`, {
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
        async deleteImage() {
            const id = this.selectedImageId;
            if (!id) {
                alert('请先选择图片');
                return;
            }
            if (!confirm('确定删除这张图片？')) return;

            try {
                const res = await fetch('/delimage/' + id + '/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: '_method=DELETE'
                });
                const data = await res.json();
                if (data.status === 'success') {
                    document.querySelector('[data-image-id="' + id + '"]')?.remove();
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
})