"""
USB条码扫描器通信模块
用于通过USB接口连接小米手机或其他条码扫描设备
"""
import serial
import threading
import time
from django.utils import timezone
from .models import BarcodeScanner


class USBScannerManager:
    """USB扫描器管理器"""
    
    def __init__(self):
        self.active_connections = {}
        self.running = False
        self.listener_thread = None
    
    def start(self):
        """启动扫描器监听"""
        if not self.running:
            self.running = True
            self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()
            print("USB扫描器监听已启动")
    
    def stop(self):
        """停止扫描器监听"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=2)
        
        # 关闭所有连接
        for device_id, connection in self.active_connections.items():
            try:
                connection.close()
            except:
                pass
        self.active_connections.clear()
        print("USB扫描器监听已停止")
    
    def _listen_loop(self):
        """监听循环"""
        while self.running:
            try:
                # 获取所有在线的扫描器
                scanners = BarcodeScanner.objects.filter(status=1)
                
                for scanner in scanners:
                    if scanner.device_id not in self.active_connections:
                        # 建立新连接
                        self._connect_scanner(scanner)
                    
                    # 读取数据
                    self._read_scanner_data(scanner)
                
                time.sleep(0.1)  # 避免CPU占用过高
                
            except Exception as e:
                print(f"扫描器监听错误: {e}")
                time.sleep(1)
    
    def _connect_scanner(self, scanner):
        """连接扫描器"""
        try:
            connection = serial.Serial(
                port=scanner.port,
                baudrate=scanner.baud_rate,
                timeout=1
            )
            self.active_connections[scanner.device_id] = connection
            scanner.status = 1
            scanner.last_active = timezone.now()
            scanner.save()
            print(f"扫描器 {scanner.name} 已连接")
            
        except Exception as e:
            print(f"连接扫描器 {scanner.name} 失败: {e}")
            scanner.status = 3  # 故障
            scanner.save()
    
    def _read_scanner_data(self, scanner):
        """读取扫描器数据"""
        if scanner.device_id not in self.active_connections:
            return
        
        connection = self.active_connections[scanner.device_id]
        
        try:
            if connection.in_waiting > 0:
                # 读取条码数据
                barcode = connection.readline().decode('utf-8').strip()
                
                if barcode:
                    # 更新最后活跃时间
                    scanner.last_active = timezone.now()
                    scanner.save()
                    
                    # 触发条码扫描事件
                    self._on_barcode_scanned(barcode, scanner)
                    
        except Exception as e:
            print(f"读取扫描器 {scanner.name} 数据失败: {e}")
            # 连接可能已断开，尝试重新连接
            try:
                connection.close()
            except:
                pass
            del self.active_connections[scanner.device_id]
            scanner.status = 2  # 离线
            scanner.save()
    
    def _on_barcode_scanned(self, barcode, scanner):
        """条码扫描事件处理"""
        print(f"扫描到条码: {barcode} (设备: {scanner.name})")
        # 这里可以触发信号或调用回调函数
        # 例如：将条码发送到前端或添加到购物车
    
    def test_connection(self, port, baud_rate=9600):
        """测试串口连接"""
        try:
            connection = serial.Serial(port=port, baudrate=baud_rate, timeout=1)
            connection.close()
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def list_available_ports(self):
        """列出可用的串口"""
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]


# 全局扫描器管理器实例
scanner_manager = USBScannerManager()
