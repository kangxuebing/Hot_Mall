"""
人脸识别工具函数
"""
try:
    import face_recognition
    import numpy as np
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    face_recognition = None
    np = None

import json
import base64
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger('django')


def decode_base64_image(base64_string):
    """
    将base64编码的图片字符串解码为PIL Image对象
    """
    try:
        # 去除可能的前缀（如 data:image/jpeg;base64,）
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # 解码base64
        image_data = base64.b64decode(base64_string)
        
        # 转换为PIL Image
        image = Image.open(BytesIO(image_data))
        
        # 转换为RGB格式（face_recognition需要RGB）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    except Exception as e:
        logger.error(f"解码base64图片失败: {e}")
        return None


def encode_face_from_image(image):
    """
    从PIL Image对象中提取人脸特征编码
    返回: 编码列表或None
    """
    if not FACE_RECOGNITION_AVAILABLE:
        logger.error("face_recognition库未安装，无法提取人脸特征")
        return None
    
    try:
        # 将PIL Image转换为numpy数组
        image_array = np.array(image)
        
        # 检测人脸
        face_locations = face_recognition.face_locations(image_array)
        
        if len(face_locations) == 0:
            logger.warning("未检测到人脸")
            return None
        
        if len(face_locations) > 1:
            logger.warning("检测到多张人脸，只使用第一张")
        
        # 提取人脸特征编码
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if len(face_encodings) > 0:
            return face_encodings[0].tolist()
        
        return None
    except Exception as e:
        logger.error(f"提取人脸特征失败: {e}")
        return None


def save_face_encoding(user, face_encoding_list):
    """
    将人脸特征编码保存到用户模型
    """
    try:
        # 将numpy数组转换为JSON字符串存储
        face_encoding_json = json.dumps(face_encoding_list)
        user.face_encoding = face_encoding_json
        user.save()
        return True
    except Exception as e:
        logger.error(f"保存人脸特征失败: {e}")
        return False


def compare_face_encoding(face_encoding_list, stored_encoding_json):
    """
    比较两个人脸特征编码
    返回: 是否匹配（布尔值）
    """
    if not FACE_RECOGNITION_AVAILABLE:
        logger.error("face_recognition库未安装，无法比较人脸特征")
        return False
    
    try:
        # 将JSON字符串转换回列表
        stored_encoding = json.loads(stored_encoding_json)
        
        # 转换为numpy数组
        face_encoding = np.array(face_encoding_list)
        stored_encoding = np.array(stored_encoding)
        
        # 比较人脸特征（tolerance参数控制匹配严格程度，默认0.6）
        matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.5)
        
        return matches[0]
    except Exception as e:
        logger.error(f"比较人脸特征失败: {e}")
        return False


def find_user_by_face(face_encoding_list):
    """
    根据人脸特征查找用户
    返回: User对象或None
    """
    if not FACE_RECOGNITION_AVAILABLE:
        logger.error("face_recognition库未安装，无法查找用户")
        return None
    
    from .models import User
    
    try:
        # 获取所有已注册人脸的用户
        users = User.objects.exclude(face_encoding__isnull=True).exclude(face_encoding__exact='')
        
        face_encoding = np.array(face_encoding_list)
        
        for user in users:
            if user.face_encoding:
                stored_encoding = json.loads(user.face_encoding)
                stored_encoding = np.array(stored_encoding)
                
                # 比较人脸特征
                matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.5)
                
                if matches[0]:
                    return user
        
        return None
    except Exception as e:
        logger.error(f"根据人脸查找用户失败: {e}")
        return None
