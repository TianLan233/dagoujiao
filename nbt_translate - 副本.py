import re
import json
import sys

# 排除词列表：如果 id 键的值在此列表中，该条目将被自动删除
EXCLUDE_IDS = [
    # 在这里添加需要排除的 id 值
    # 例如："minecraft:empty", "minecraft:air"
    "minecraft:generic.knockback_resistance",
    "minecraft:generic.scale",
]

class NBTToJSONConverter:
    """将 Minecraft NBT 格式数据转换为标准 JSON"""
    
    def __init__(self):
        self.pos = 0
        self.text = ""
    
    def extract_entity_data(self, input_text):
        """从输入文本中提取 entity_data= 之后的内容"""
        match = re.search(r'entity_data=\{', input_text)
        if not match:
            raise ValueError("未找到 entity_data= 标记")
        
        start = match.start()
        # 找到匹配的右括号
        brace_count = 0
        in_string = False
        string_char = None
        escape_next = False
        
        for i in range(match.end() - 1, len(input_text)):
            char = input_text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if in_string:
                if char == string_char:
                    in_string = False
                continue
            
            if char in '"\'':
                in_string = True
                string_char = char
                continue
            
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return input_text[match.end() - 1:i + 1]
        
        raise ValueError("未找到匹配的右括号")
    
    def parse_nbt(self, text):
        """解析 NBT 文本"""
        self.text = text
        self.pos = 0
        self.skip_whitespace()
        return self.parse_value()
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            self.pos += 1
    
    def parse_value(self):
        """解析 NBT 值"""
        self.skip_whitespace()
        
        if self.pos >= len(self.text):
            return None
        
        char = self.text[self.pos]
        
        # 对象
        if char == '{':
            return self.parse_object()
        
        # 数组
        if char == '[':
            return self.parse_array()
        
        # 字符串（双引号或单引号）
        if char in '"\'':
            return self.parse_string()
        
        # 数字或布尔值
        return self.parse_number_or_bool()
    
    def parse_object(self):
        """解析 NBT 对象"""
        result = {}
        self.pos += 1  # 跳过 {
        self.skip_whitespace()
        
        while self.pos < len(self.text) and self.text[self.pos] != '}':
            # 跳过逗号
            if self.text[self.pos] == ',':
                self.pos += 1
                self.skip_whitespace()
                continue
            
            # 解析键
            key = self.parse_key()
            
            self.skip_whitespace()
            
            # 跳过冒号
            if self.pos < len(self.text) and self.text[self.pos] == ':':
                self.pos += 1
            
            self.skip_whitespace()
            
            # 解析值
            value = self.parse_value()
            result[key] = value
            
            self.skip_whitespace()
        
        if self.pos < len(self.text):
            self.pos += 1  # 跳过 }
        
        return result
    
    def parse_key(self):
        """解析 NBT 对象的键"""
        self.skip_whitespace()
        
        if self.pos >= len(self.text):
            return ""
        
        char = self.text[self.pos]
        
        # 带引号的键
        if char in '"\'':
            return self.parse_string()
        
        # 不带引号的键
        key = ""
        while self.pos < len(self.text) and self.text[self.pos] not in ':,{}[] \t\n\r':
            key += self.text[self.pos]
            self.pos += 1
        
        return key
    
    def parse_string(self):
        """解析字符串"""
        if self.pos >= len(self.text):
            return ""
        
        quote_char = self.text[self.pos]
        self.pos += 1
        
        result = ""
        while self.pos < len(self.text) and self.text[self.pos] != quote_char:
            if self.text[self.pos] == '\\' and self.pos + 1 < len(self.text):
                self.pos += 1
                escape_char = self.text[self.pos]
                if escape_char == 'n':
                    result += '\n'
                elif escape_char == 't':
                    result += '\t'
                elif escape_char == 'r':
                    result += '\r'
                elif escape_char == '\\':
                    result += '\\'
                elif escape_char == '"':
                    result += '"'
                elif escape_char == "'":
                    result += "'"
                else:
                    result += '\\' + escape_char
            else:
                result += self.text[self.pos]
            
            self.pos += 1
        
        if self.pos < len(self.text):
            self.pos += 1  # 跳过结束引号
        
        # 检查是否是嵌套的 JSON 字符串
        if result.strip().startswith('{') or result.strip().startswith('['):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                pass
        
        return result
    
    def parse_array(self):
        """解析数组"""
        self.pos += 1  # 跳过 [
        self.skip_whitespace()
        
        if self.pos >= len(self.text):
            return []
        
        # 检查是否是类型化数组 [I; ...], [B; ...], [L; ...], [D; ...], [F; ...]
        if self.pos < len(self.text) and self.text[self.pos] in 'IBLDF':
            array_type = self.text[self.pos]
            self.pos += 1
            
            if self.pos < len(self.text) and self.text[self.pos] == ';':
                self.pos += 1  # 跳过 ;
                return self.parse_typed_array(array_type)
            else:
                # 回退
                self.pos -= 1
        
        return self.parse_normal_array()
    
    def parse_typed_array(self, array_type):
        """解析类型化数组"""
        result = []
        self.skip_whitespace()
        
        while self.pos < len(self.text) and self.text[self.pos] != ']':
            if self.text[self.pos] == ',':
                self.pos += 1
                self.skip_whitespace()
                continue
            
            # 解析数字（可能带有类型后缀）
            num_str = ""
            while self.pos < len(self.text) and self.text[self.pos] not in ',] \t\n\r':
                num_str += self.text[self.pos]
                self.pos += 1
            
            # 移除类型后缀
            num_str = num_str.rstrip('bBdDfFlLsS')
            
            if num_str:
                try:
                    if '.' in num_str:
                        result.append(float(num_str))
                    else:
                        result.append(int(num_str))
                except ValueError:
                    result.append(num_str)
            
            self.skip_whitespace()
        
        if self.pos < len(self.text):
            self.pos += 1  # 跳过 ]
        
        return result
    
    def parse_normal_array(self):
        """解析普通数组"""
        result = []
        self.skip_whitespace()
        
        while self.pos < len(self.text) and self.text[self.pos] != ']':
            if self.text[self.pos] == ',':
                self.pos += 1
                self.skip_whitespace()
                continue
            
            value = self.parse_value()
            if value is not None:
                result.append(value)
            
            self.skip_whitespace()
        
        if self.pos < len(self.text):
            self.pos += 1  # 跳过 ]
        
        return result
    
    def parse_number_or_bool(self):
        """解析数字或布尔值"""
        num_str = ""
        
        while self.pos < len(self.text) and self.text[self.pos] not in ',{}[] \t\n\r':
            num_str += self.text[self.pos]
            self.pos += 1
        
        # 检查布尔值
        if num_str.lower() in ('true', '1b'):
            return True
        if num_str.lower() in ('false', '0b'):
            return False
        
        # 移除类型后缀
        clean_num = num_str.rstrip('bBdDfFlLsS')
        
        if not clean_num:
            return num_str
        
        # 尝试解析为数字
        try:
            if '.' in clean_num:
                return float(clean_num)
            else:
                return int(clean_num)
        except ValueError:
            return num_str


def filter_excluded_ids(data, exclude_ids):
    """递归过滤包含排除 id 的对象"""
    if not exclude_ids:
        return data
    
    if isinstance(data, dict):
        # 检查当前字典是否有 id 键且值在排除列表中
        if 'id' in data and data['id'] in exclude_ids:
            return None  # 返回 None 表示删除此对象
        
        # 递归处理字典的每个值
        filtered = {}
        for key, value in data.items():
            filtered_value = filter_excluded_ids(value, exclude_ids)
            if filtered_value is not None:
                filtered[key] = filtered_value
        
        return filtered
    
    elif isinstance(data, list):
        # 递归处理列表，过滤掉返回 None 的项
        filtered = []
        for item in data:
            filtered_item = filter_excluded_ids(item, exclude_ids)
            if filtered_item is not None:
                filtered.append(filtered_item)
        return filtered
    
    else:
        # 其他类型直接返回
        return data


def convert_nbt_to_json(input_file, output_file, exclude_ids=None):
    """将 NBT 文件转换为 JSON 文件"""
    if exclude_ids is None:
        exclude_ids = EXCLUDE_IDS
    
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        input_text = f.read()
    
    # 创建转换器
    converter = NBTToJSONConverter()
    
    # 提取 entity_data
    nbt_text = converter.extract_entity_data(input_text)
    
    # 解析 NBT
    data = converter.parse_nbt(nbt_text)
    
    # 过滤排除的 id
    if exclude_ids:
        data = filter_excluded_ids(data, exclude_ids)
        print(f"已应用排除词列表：{exclude_ids}")
    
    # 写入 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"成功转换！输出文件：{output_file}")


if __name__ == "__main__":
    input_file = "input.txt"
    output_file = "output.json"
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    try:
        convert_nbt_to_json(input_file, output_file)
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)