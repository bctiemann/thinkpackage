from Crypto import Random
from Crypto.Cipher import AES
import base64
import hashlib

class AESCipher(object):

    def __init__(self, key):
        self.bs = 32
        self.key = base64.b64decode(key)

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = enc.decode('hex')
        iv = AES.block_size * '\x00'
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(enc[0:AES.block_size])
#        return self._unpad(cipher.decrypt(enc[0:AES.block_size:])).decode('utf-8')
        return decrypted

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]
