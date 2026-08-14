$(function () {
    // 使用base.html中的统一#app容器
    const app = document.getElementById('app');
    if (!app) return;
    
    // 检查是否是幸运大转盘页面
    const viewData = app.querySelector('[data-view="lottery-wheel"]');
    if (!viewData) return;
    
    // Vue应用实例
    new Vue({
        el: '#app',
        data: {
            prizesData: [],
            csrfToken: '',
            drawUrl: '',
            isSpinning: false,
            currentRotation: 0,
            pointerRotation: 0
        },
        methods: {
            drawWheel: function() {
                const canvas = document.getElementById('wheelCanvas');
                const ctx = canvas.getContext('2d');
                const centerX = canvas.width / 2;
                const centerY = canvas.height / 2;
                const radius = canvas.width / 2;
                
                const prizes = this.prizesData;
                const numPrizes = prizes.length;
                const arcSize = (2 * Math.PI) / numPrizes; // 每个奖项扇形大小相同
                
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                prizes.forEach((prize, index) => {
                    const startAngle = index * arcSize - Math.PI / 2;
                    const endAngle = startAngle + arcSize;
                    
                    // 保存每个奖项的角度范围，用于指针定位
                    prize.startAngle = startAngle;
                    prize.endAngle = endAngle;
                    prize.arcSize = arcSize;
                    
                    // 绘制扇形
                    ctx.beginPath();
                    ctx.moveTo(centerX, centerY);
                    ctx.arc(centerX, centerY, radius, startAngle, endAngle);
                    ctx.closePath();
                    ctx.fillStyle = prize.color;
                    ctx.globalAlpha = 0.8; // 设置透明度
                    ctx.fill();
                    ctx.globalAlpha = 1.0; // 恢复不透明
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    
                    // 绘制文字
                    ctx.save();
                    ctx.translate(centerX, centerY);
                    ctx.rotate(startAngle + arcSize / 2);
                    ctx.textAlign = 'right';
                    ctx.fillStyle = '#fff';
                    ctx.font = 'bold 14px Arial';
                    ctx.fillText(prize.name, radius - 20, 5);
                    ctx.restore();
                });
            },
            
            drawPointer: function(rotation) {
                const canvas = document.getElementById('wheelCanvas');
                const ctx = canvas.getContext('2d');
                const centerX = canvas.width / 2;
                const centerY = canvas.height / 2;
                const radius = canvas.width / 2;
                
                ctx.save();
                ctx.translate(centerX, centerY);
                ctx.rotate(rotation);

                // ==========【完整柄+箭头组合指针】==========
                // 1. 指针柄（从中心点延伸到箭头底部）
                const handleLength = 25; // 柄的长度
                const handleWidth = 12;  // 柄的宽度

                // 2. 箭头部分（从柄末端延伸到转盘边缘）
                const arrowLength = 50;  // 箭头长度（增加长度）
                const arrowWidth = 24;   // 箭头最大宽度

                // 创建渐变填充（柄到箭头自然过渡）
                const pointerGrad = ctx.createLinearGradient(0, 0, 0, -handleLength - arrowLength);
                pointerGrad.addColorStop(0, '#d60000');    // 柄部颜色（深）
                pointerGrad.addColorStop(0.5, '#ff3333');  // 过渡色
                pointerGrad.addColorStop(1, '#ff4444');    // 箭头颜色（浅）

                // 绘制完整指针路径（柄+箭头一体化）
                ctx.beginPath();
                // 柄部左侧
                ctx.moveTo(-handleWidth/2, 0);
                ctx.lineTo(-handleWidth/2, -handleLength);
                // 箭头左侧
                ctx.lineTo(-arrowWidth/2, -handleLength - arrowLength/2);
                // 箭头尖端（指向转盘）
                ctx.lineTo(0, -handleLength - arrowLength);
                // 箭头右侧
                ctx.lineTo(arrowWidth/2, -handleLength - arrowLength/2);
                // 柄部右侧
                ctx.lineTo(handleWidth/2, -handleLength);
                ctx.lineTo(handleWidth/2, 0);
                ctx.closePath();

                // 指针样式设置
                ctx.fillStyle = pointerGrad;
                ctx.shadowColor = 'rgba(0,0,0,0.35)';
                ctx.shadowBlur = 12;
                ctx.shadowOffsetY = 4;
                ctx.fill();
                ctx.shadowBlur = 0;
                ctx.shadowOffsetY = 0;
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();

                // 3. 中心固定圆点（双层同心圆，增强精致感）
                // 外圈（与柄部颜色一致）
                ctx.beginPath();
                ctx.arc(0, 0, 14, 0, 2 * Math.PI);
                ctx.fillStyle = '#d60000';
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 3;
                ctx.stroke();
                // 内小白点（高光效果）
                ctx.beginPath();
                ctx.arc(0, 0, 5, 0, 2 * Math.PI);
                ctx.fillStyle = '#ffffff';
                ctx.fill();

                ctx.restore();
            },

            spin: function() {
                if (this.isSpinning) return;

                this.isSpinning = true;
                const spinBtn = document.getElementById('spinBtn');
                spinBtn.disabled = true;

                // 调用后端API进行抽奖
                $.ajax({
                    url: this.drawUrl,
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.csrfToken
                    },
                    success: (data) => {
                        if (data.code === 0) {
                            const winIndex = data.data.index;
                            const targetPrize = this.prizesData[winIndex];

                            console.log('中奖索引:', winIndex);
                            console.log('目标奖项:', targetPrize);
                            console.log('奖项角度范围:', targetPrize.startAngle, targetPrize.endAngle);

                            // 计算指针需要旋转的角度
                            // 指针初始指向顶部（-90度），需要旋转到目标扇形中心
                            const targetAngle = targetPrize.startAngle + targetPrize.arcSize / 2;
                            const initialAngle = -Math.PI / 2; // 指针初始角度（顶部）
                            const rotationNeeded = targetAngle - initialAngle;
                            
                            console.log('目标角度:', targetAngle);
                            console.log('需要旋转角度:', rotationNeeded);
                            
                            // 指针需要旋转的总角度（加上5圈旋转）
                            const totalRotation = (Math.PI * 2 * 5) + rotationNeeded;

                            console.log('总旋转角度:', totalRotation);

                            let currentRotation = 0;
                            const duration = 5000; // 5秒
                            const startTime = Date.now();

                            const animate = () => {
                                const elapsed = Date.now() - startTime;
                                const progress = Math.min(elapsed / duration, 1);

                                // 缓动函数
                                const easeOut = 1 - Math.pow(1 - progress, 3);
                                currentRotation = totalRotation * easeOut;

                                // 重绘转盘（静止）
                                this.drawWheel();

                                // 绘制旋转的指针
                                this.drawPointer(currentRotation);

                                if (progress < 1) {
                                    requestAnimationFrame(animate);
                                } else {
                                    this.isSpinning = false;
                                    spinBtn.disabled = false;
                                    alert(`恭喜您获得：${targetPrize.name}！`);
                                }
                            };

                            animate();
                        } else {
                            this.isSpinning = false;
                            spinBtn.disabled = false;
                            alert(data.msg || '抽奖失败，请重试');
                        }
                    },
                    error: (error) => {
                        this.isSpinning = false;
                        spinBtn.disabled = false;
                        alert('抽奖失败，请重试');
                    }
                });
            },
        },
        mounted: function() {
            // 从模板中获取数据
            const viewData = this.$el.querySelector('[data-view="lottery-wheel"]');
            if (viewData) {
                this.csrfToken = viewData.getAttribute('data-csrf-token');
                this.drawUrl = viewData.getAttribute('data-draw-url');
                this.prizesData = JSON.parse(viewData.getAttribute('data-prizes'));

                // 初始化绘制转盘
                this.drawWheel();
                // 初始化绘制指针（旋转角度为0）
                this.drawPointer(0);
            }
        }
    });
});