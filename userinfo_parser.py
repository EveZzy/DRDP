import io
import base64
import os

class MMKVReader:
    def __init__(self, reader):
        self.reader = reader
        self.pos = 0
        self.buffer = bytearray(8)

    def get_pos(self):
        return self.pos

    def read_data(self, size):
        data = self.reader.read(size)
        if len(data) != size:
            if not data:
                raise EOFError("读取错误")
            else:
                raise IOError("读取错误")
        self.pos += len(data)
        return data

    def read_byte_data(self):
        data = self.read_data(1)
        self.buffer[0:1] = data
        return self.buffer[0]

    def read_int32_data(self):
        data = self.read_data(4)
        self.buffer[0:4] = data
        result = (self.buffer[3] << 24) | (self.buffer[2] << 16) | (self.buffer[1] << 8) | self.buffer[0]
        return result

class MMKV:
    def __init__(self, reader):
        self.reader = MMKVReader(reader)
        self.data = {}
        self.decode()

    def decode(self):
        try:
            self.reader.read_int32_data()
            MMKVReadRawVarint32(self.reader)
            while True:
                key = read_key(self.reader)
                value = read_value(self.reader)
                key = key.decode('utf-8')
                # print(key)
                if not value:
                    del self.data[key]
                else:
                    self.data[key] = value            
        except Exception as e:
            print(f"Error during decoding: {e}")
            pass


    def get(self, key):
        return self.data.get(key, b"")

def read_key(reader):
    count = MMKVReadRawVarint32(reader)
    if count > 4096:
        return b""
    buffer = reader.read_data(count)
    return buffer

def read_value(reader):
    count = MMKVReadRawVarint32(reader)
    if 0 < count < 4096:
        value = reader.read_data(count)
        return value

def MMKVReadRawVarint32(reader):
    num = 0
    for i in range(5):
        b = reader.read_byte_data()
        num |= (b & 0x7F) << (i * 7)
        if b <= 0x7F:
            return num
    for i in range(5):
        if reader.read_byte_data() <= 0x7F:
            break
    return num

def ParseUserInfos():
    root_path = r"./mmkvs" # 需要解析的mmkv文件放到mmkvs目录下，可实现批量解析
    fls = os.listdir(root_path)
    for fl in fls:
        if not fl.endswith('.default'): # 判断文件名后缀是不是.default，如果不是则不做处理
            continue
        full_path = os.path.join(root_path,fl)
        print('需要解析的mmkv文件路径： ',full_path)
        dfile = open(os.path.join(root_path,fl+".txt"),"w")
        try:
            with open(full_path, "rb") as file:
                mmv = MMKV(file)
                for key in ["key_account_nickname", "key_account_id", "key_account_email",
                            "key_account_phone", "key_account_uid", "key_account_phone_area"]:
                    result = base64.standard_b64decode(mmv.get(key)[1:]).decode("utf-8")
                    # print(f"{key}: {result}")
                    dfile.write(f"{key}: {result}")
                    dfile.write("\n")
        except Exception as e:
            print(f"Read File Error: {e}")

        dfile.close()

if __name__ == "__main__":
    ParseUserInfos()
