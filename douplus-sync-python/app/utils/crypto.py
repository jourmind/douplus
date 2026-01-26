"""
加密解密工具
"""
import base64


def decrypt_access_token(encrypted_token: str) -> str:
    """
    解密AccessToken
    Java使用Base64编码存储,Python直接解码即可
    
    Args:
        encrypted_token: Base64编码的token
    
    Returns:
        解密后的token
    """
    try:
        decoded_bytes = base64.b64decode(encrypted_token)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"解密token失败: {e}")


def encrypt_access_token(token: str) -> str:
    """
    加密AccessToken
    
    Args:
        token: 原始token
    
    Returns:
        Base64编码的token
    """
    encoded_bytes = token.encode('utf-8')
    return base64.b64encode(encoded_bytes).decode('utf-8')
