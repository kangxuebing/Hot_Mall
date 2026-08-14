import re

# 邮件验证链接有效期：一天
VERIFY_EMAIL_TOKEN_EXPIRES = 60 * 60 * 24

# 用户密码：8～20 位，须含数字、小写、大写、特殊字符（非字母数字且非空白，如 @ _ ! 等）
# 使用 [^\s] 与「非字母数字」前瞻，避免 Python/JS 对 [] 转义不一致导致个别浏览器校验失败
USER_PASSWORD_REGEX = re.compile(
    r'^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9\s])[\x21-\x7E]{8,20}$'
)

# 用户地址上限
USER_ADDRESS_COUNTS_LIMIT = 20
# 显示我的订单数量
ORDERS_LIST_LIMIT = 5