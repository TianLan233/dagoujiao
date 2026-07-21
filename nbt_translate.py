import re
import json
import sys
import os
import glob

#排除词列表：如果id键的值在此列表中，该条目将被自动删除
EXCLUDE_IDS = [
    #在这里添加需要排除的id值，用于排除不具有个体差异的属性
    #例如："minecraft:empty","minecraft:air"
    "minecraft:generic.knockback_resistance",
    "minecraft:generic.scale",
    "apothic_attributes:healing_received",
    "minecraft:generic.burning_time",
    "minecraft:generic.oxygen_bonus",
    "minecraft:generic.follow_range",

]

#翻译对照表：将原始键名替换为中文名称
KEY_TRANSLATION = {
    #在这里添加需要翻译的键名
    "apotheosis:armor/dmg_reduction/blockading":"物理减伤",
    "apotheosis:armor/dmg_reduction/runed":"魔法减伤",
    "apotheosis:armor/dmg_reduction/blast_forged":"爆炸减伤",
    "apotheosis:armor/dmg_reduction/deflective":"弹射物减伤",
    "apotheosis:armor/attribute/blessed":"生命值",
    "apotheosis:armor/attribute/ironforged":"护甲值",
    "apotheosis:armor/attribute/adamantine":"护甲百分比",
    "apotheosis:armor/attribute/steel_touched":"韧性值",
    "apotheosis:generic/attribute/lucky":"大幸运值",
    "apotheosis:generic/attribute/fortunate":"小幸运值",
    "apotheosis:armor/attribute/stalwart":"击退抗性",
    "apotheosis:armor/mob_effect/bolstering":"抗性提升",
    "apotheosis:melee/attribute/graceful":"攻速",
    "apotheosis:melee/attribute/vampiric":"吸血",
    "apotheosis:melee/attribute/berserking":"过量治疗",
    "apotheosis:melee/attribute/giant_slaying":"生命值伤害",
    "apotheosis:melee/attribute/violent":"伤害值",
    "apotheosis:melee/attribute/murderous":"伤害百分比",
    "apotheosis:melee/attribute/infernal":"火伤",
    "apotheosis:melee/attribute/glacial":"冰伤",
    "apotheosis:melee/attribute/forceful":"击退",
    "apotheosis:melee/attribute/piercing":"盔甲穿透",
    "apotheosis:melee/attribute/intricate":"暴率",
    "apotheosis:melee/attribute/lacerating":"暴伤",
    "apotheosis:melee/cleaving":"挥劈",
    "apotheosis:melee/executing":"处刑",
    "apotheosis:melee/thunderstruck":"雷鸣",
    "apotheosis:melee/mob_effect/caustic":"腐蚀",
    "apotheosis:melee/mob_effect/bloodletting":"放血",
    "apotheosis:melee/mob_effect/festive":"节庆",
    "apotheosis:melee/mob_effect/elusive":"灵巧",
    "apotheosis:shield/attribute/ironforged":"护甲百分比",
    "apotheosis:shield/attribute/stelltouched":"韧性百分比",
    "apotheosis:shield/attribute/stalwart":"击退抗性",
}

#数值区间列表：定义属性的数值区间[最小值,最大值]，修正值0.0对应最小值，修正值1.0对应最大值
VALUE_RANGES = {
    #在这里添加需要转换的属性及其数值区间
    "apotheosis:armor/dmg_reduction/blockading": [0.05, 0.15],
    "apotheosis:armor/dmg_reduction/runed": [0.05, 0.15],
    "apotheosis:armor/dmg_reduction/blast_forged": [0.15, 0.35],
    "apotheosis:armor/dmg_reduction/deflective": [0.15, 0.30],
    "apotheosis:armor/attribute/blessed":[5,8],
    "apotheosis:armor/attribute/ironforged":[4,8],
    "apotheosis:armor/attribute/adamantine":[0.25,0.4],
    "apotheosis:armor/attribute/steel_touched":[2,6],
    "apotheosis:generic/attribute/lucky":[3,6],
    "apotheosis:generic/attribute/fortunate":[3,5],
    "apotheosis:armor/attribute/stalwart":[0.25,0.35],
    "apotheosis:melee/attribute/vampiric":[0.10,0.15],
    "apotheosis:melee/attribute/berserking":[0.15,0.25],
    "apotheosis:melee/attribute/giant_slaying":[0.10,0.25],
    "apotheosis:melee/attribute/violent":[5,8],
    "apotheosis:melee/attribute/murderous":[0.25,0.55],
    "apotheosis:melee/attribute/infernal":[4,10],
    "apotheosis:melee/attribute/glacial":[4,10],
    "apotheosis:melee/attribute/intricate":[0.25,0.55],
    "apotheosis:melee/attribute/lacerating":[0.25,0.40],
    "apotheosis:melee/cleaving":[0.4,0.6],
    "apotheosis:melee/executing":[0.15,0.25],
    "apotheosis:melee/thunderstruck":[4,8],
    "apotheosis:melee/mob_effect/festive":[0.03,0.06],
    "apotheosis:shield/attribute/ironforged":[0.2,0.3],
    "apotheosis:shield/attribute/stelltouched":[0.2,0.3],
    "apotheosis:shield/attribute/stalwart":[0.25,0.35],
}

#删除键名列表：在导出前删除这些键名及其对应键值
REMOVE_KEYS = [
    #在这里添加需要删除的键名
    "Age",
    "Air",
    "AngerTime",
    "AngryAt",
    "Brain",
    "CanPickUpLoot",
    "CollarColor",
    "CustomNameVisible",
    "DeathLootTable",
    "DeathTime",
    "FallDistance",
    "FallFlying",
    "Fire",
    "ForcedAge",
    "HurtTime",
    "HurtByTimestamp",
    "Invulnerable",
    "LeftHanded",
    "PersistenceRequired",
    "InLove",
    "Motion",
    "NeoForgeData",
    "OnGround",
    "Owner",
    "PortalCooldown",
    "Pos",
    "Rotation",
    "Sitting",
    "neoforge:attachments",
    "supplementaries:slimed_data",
    "twilightforest:last_damage_armor_time",
    "twilightforest:slimy_soles_bounce_info",
    "yes_steve_model:vehicle_model_id",
    "apotheosis:affix_name",
    #"attributes",
    "minecraft:custom_name",
    "apotheosis:durability_bonus",
    "apotheosis:from_boss",
    "apotheosis:rarity",
    "count",
    "minecraft:enchantments",
    "ArmorDropChances",
    "HandDropChances",
]

class NBTToJSONConverter:
    """将Minecraft NBT格式数据转换为标准JSON"""
    
    def __init__(self):
        self.pos = 0
        self.text = ""
    
    def extract_entity_data(self, input_text):
        """从输入文本中提取data=或mob_imprisonment=之后的内容"""
        # 尝试匹配 data= 或 mob_imprisonment=
        match = re.search(r'(?:data|mob_imprisonment)=\{', input_text)
        if not match:
            raise ValueError("未找到data=或mob_imprisonment=标记")
        
        start = match.start()
        #找到匹配的右括号
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
        """解析NBT文本"""
        self.text = text
        self.pos = 0
        self.skip_whitespace()
        return self.parse_value()
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            self.pos += 1
    
    def parse_value(self):
        """解析NBT值"""
        self.skip_whitespace()
        
        if self.pos >= len(self.text):
            return None
        
        char = self.text[self.pos]
        
        #对象
        if char == '{':
            return self.parse_object()
        
        #数组
        if char == '[':
            return self.parse_array()
        
        #字符串（双引号或单引号）
        if char in '"\'':
            return self.parse_string()
        
        #数字或布尔值
        return self.parse_number_or_bool()
    
    def parse_object(self):
        """解析NBT对象"""
        result = {}
        self.pos += 1  #跳过{
        self.skip_whitespace()
        
        while self.pos < len(self.text) and self.text[self.pos] != '}':
            #跳过逗号
            if self.text[self.pos] == ',':
                self.pos += 1
                self.skip_whitespace()
                continue
            
            #解析键
            key = self.parse_key()
            
            self.skip_whitespace()
            
            #跳过冒号
            if self.pos < len(self.text) and self.text[self.pos] == ':':
                self.pos += 1
            
            self.skip_whitespace()
            
            #解析值
            value = self.parse_value()
            result[key] = value
            
            self.skip_whitespace()
        
        if self.pos < len(self.text):
            self.pos += 1  #跳过}
        
        return result
    
    def parse_key(self):
        """解析NBT对象的键"""
        self.skip_whitespace()
        
        if self.pos >= len(self.text):
            return ""
        
        char = self.text[self.pos]
        
        #带引号的键
        if char in '"\'':
            return self.parse_string()
        
        #不带引号的键
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
            self.pos += 1  #跳过结束引号
        
        #检查是否是嵌套的JSON字符串
        if result.strip().startswith('{') or result.strip().startswith('['):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                pass
        
        return result
    
    def parse_array(self):
        """解析数组"""
        self.pos += 1  #跳过[
        self.skip_whitespace()
        
        if self.pos >= len(self.text):
            return []
        
        #检查是否是类型化数组[I;...],[B;...],[L;...],[D;...],[F;...]
        if self.pos < len(self.text) and self.text[self.pos] in 'IBLDF':
            array_type = self.text[self.pos]
            self.pos += 1
            
            if self.pos < len(self.text) and self.text[self.pos] == ';':
                self.pos += 1  #跳过;
                return self.parse_typed_array(array_type)
            else:
                #回退
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
            
            #解析数字（可能带有类型后缀）
            num_str = ""
            while self.pos < len(self.text) and self.text[self.pos] not in ',] \t\n\r':
                num_str += self.text[self.pos]
                self.pos += 1
            
            #移除类型后缀
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
            self.pos += 1  #跳过]
        
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
            self.pos += 1  #跳过]
        
        return result
    
    def parse_number_or_bool(self):
        """解析数字或布尔值"""
        num_str = ""
        
        while self.pos < len(self.text) and self.text[self.pos] not in ',{}[] \t\n\r':
            num_str += self.text[self.pos]
            self.pos += 1
        
        #检查布尔值
        if num_str.lower() in ('true', '1b'):
            return True
        if num_str.lower() in ('false', '0b'):
            return False
        
        #移除类型后缀
        clean_num = num_str.rstrip('bBdDfFlLsS')
        
        if not clean_num:
            return num_str
        
        #尝试解析为数字
        try:
            if '.' in clean_num:
                return float(clean_num)
            else:
                return int(clean_num)
        except ValueError:
            return num_str


def apply_value_ranges(data, value_ranges, in_affixes=False):
    """根据数值区间计算实际值，仅对apotheosis:affixes下的内容生效"""
    if not value_ranges:
        return data
    
    if isinstance(data, dict):
        #检查当前键是否是apotheosis:affixes
        if 'apotheosis:affixes' in data:
            #对affixes下的内容应用数值区间
            result = {}
            for key, value in data.items():
                if key == 'apotheosis:affixes':
                    result[key] = apply_value_ranges(value, value_ranges, in_affixes=True)
                else:
                    result[key] = apply_value_ranges(value, value_ranges, in_affixes=False)
            return result
        
        #如果在affixes下，直接对键值对进行转换
        if in_affixes:
            result = {}
            for key, value in data.items():
                if key in value_ranges and isinstance(value, (int, float)):
                    min_val, max_val = value_ranges[key]
                    #线性插值计算实际值
                    actual_value = min_val + (max_val - min_val) * value
                    result[key] = actual_value
                else:
                    result[key] = apply_value_ranges(value, value_ranges, in_affixes)
            return result
        
        #递归处理字典的每个值
        result = {}
        for key, value in data.items():
            result[key] = apply_value_ranges(value, value_ranges, in_affixes)
        return result
    
    elif isinstance(data, list):
        return [apply_value_ranges(item, value_ranges, in_affixes) for item in data]
    
    else:
        return data


def filter_drop_items(data):
    """根据DropChances过滤ArmorItems和HandItems"""
    if isinstance(data, dict):
        #处理ArmorItems
        if 'ArmorItems' in data and 'ArmorDropChances' in data:
            items = data['ArmorItems']
            chances = data['ArmorDropChances']
            if isinstance(items, list) and isinstance(chances, list):
                filtered_items = []
                for i, item in enumerate(items):
                    chance = chances[i] if i < len(chances) else 0.0
                    if chance != 0.0 and isinstance(item, dict):
                        #保留全部内容
                        filtered_items.append(item)
                    elif isinstance(item, dict):
                        #仅保留id和原有的enchantments
                        enchantments = {}
                        if 'components' in item and isinstance(item['components'], dict):
                            if 'minecraft:enchantments' in item['components']:
                                enchantments = item['components']['minecraft:enchantments']
                        filtered_items.append({'id': item['id'], 'components': {'minecraft:enchantments': enchantments}})
                    else:
                        filtered_items.append(item)
                data['ArmorItems'] = filtered_items
        
        #处理HandItems
        if 'HandItems' in data and 'HandDropChances' in data:
            items = data['HandItems']
            chances = data['HandDropChances']
            if isinstance(items, list) and isinstance(chances, list):
                filtered_items = []
                for i, item in enumerate(items):
                    chance = chances[i] if i < len(chances) else 0.0
                    if chance != 0.0 and isinstance(item, dict):
                        #保留全部内容
                        filtered_items.append(item)
                    elif isinstance(item, dict):
                        #仅保留id和原有的enchantments
                        enchantments = {}
                        if 'components' in item and isinstance(item['components'], dict):
                            if 'minecraft:enchantments' in item['components']:
                                enchantments = item['components']['minecraft:enchantments']
                        filtered_items.append({'id': item['id'], 'components': {'minecraft:enchantments': enchantments}})
                    else:
                        filtered_items.append(item)
                data['HandItems'] = filtered_items
        
        #递归处理字典的每个值
        for key, value in data.items():
            data[key] = filter_drop_items(value)
        
        return data
    
    elif isinstance(data, list):
        return [filter_drop_items(item) for item in data]
    
    else:
        return data


def format_custom_name(data):
    """格式化CustomName为完整的格式化字体字符串"""
    if isinstance(data, dict):
        #处理CustomName
        if 'CustomName' in data and isinstance(data['CustomName'], dict):
            custom_name = data['CustomName']
            
            #处理extra数组
            if 'extra' in custom_name and isinstance(custom_name['extra'], list):
                result_parts = []
                for part in custom_name['extra']:
                    if isinstance(part, dict):
                        part_str = ""
                        #添加bold标记
                        if part.get('bold') == True:
                            part_str += "&l"
                        #添加italic标记
                        if part.get('italic') == True:
                            part_str += "&r"
                        #添加颜色
                        if 'color' in part:
                            color = part['color']
                            if isinstance(color, str) and color.startswith('#'):
                                part_str += "&#" + color[1:]
                        #添加文本
                        if 'text' in part:
                            part_str += part['text']
                        result_parts.append(part_str)
                    elif isinstance(part, str):
                        result_parts.append(part)
                
                #替换extra为字符串
                custom_name['extra'] = ''.join(result_parts)
            elif 'text' in custom_name:
                #如果没有extra只有text
                prefix = ""
                if custom_name.get('bold') == True:
                    prefix += "&l"
                if custom_name.get('italic') == True:
                    prefix += "&r"
                if 'color' in custom_name:
                    color = custom_name['color']
                    if isinstance(color, str) and color.startswith('#'):
                        prefix += "&#" + color[1:]
                data['CustomName'] = prefix + custom_name['text']
        
        #递归处理字典的每个值
        for key, value in data.items():
            data[key] = format_custom_name(value)
        
        return data
    
    elif isinstance(data, list):
        return [format_custom_name(item) for item in data]
    
    else:
        return data


def translate_keys(data, translation_table):
    """递归翻译字典的键名"""
    if not translation_table:
        return data
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            #翻译键名
            new_key = translation_table.get(key, key)
            #递归处理值
            result[new_key] = translate_keys(value, translation_table)
        return result
    
    elif isinstance(data, list):
        return [translate_keys(item, translation_table) for item in data]
    
    else:
        return data


def remove_keys(data, keys_to_remove):
    """递归删除指定的键名"""
    if not keys_to_remove:
        return data
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key not in keys_to_remove:
                result[key] = remove_keys(value, keys_to_remove)
        return result
    
    elif isinstance(data, list):
        return [remove_keys(item, keys_to_remove) for item in data]
    
    else:
        return data


def calculate_attribute_modifiers(data):
    """计算属性修饰符的总效果"""
    if isinstance(data, dict):
        #检查是否是包含modifiers的属性对象
        if 'modifiers' in data and isinstance(data['modifiers'], list) and 'base' in data:
            base = data['base']
            modifiers = data['modifiers']
            
            sum_add_value = 0.0
            sum_add_multiplied_base = 0.0
            product_add_multiplied_total = 1.0
            
            for mod in modifiers:
                if isinstance(mod, dict) and 'operation' in mod and 'amount' in mod:
                    amount = mod['amount']
                    operation = mod['operation']
                    
                    if operation == 'add_value':
                        sum_add_value += amount
                    elif operation == 'add_multiplied_base':
                        sum_add_multiplied_base += amount
                    elif operation == 'add_multiplied_total':
                        product_add_multiplied_total *= (1 + amount)
            
            #计算total_amount
            total_amount = ((base + sum_add_value) * (1 + sum_add_multiplied_base) * product_add_multiplied_total)
            
            #创建新的对象，只保留id和total_amount
            return {
                'id': data['id'],
                'total_amount': total_amount
            }
        
        #递归处理字典的每个值
        result = {}
        for key, value in data.items():
            result[key] = calculate_attribute_modifiers(value)
        return result
    
    elif isinstance(data, list):
        return [calculate_attribute_modifiers(item) for item in data]
    
    else:
        return data


def filter_excluded_ids(data, exclude_ids):
    """递归过滤包含排除id的对象"""
    if not exclude_ids:
        return data
    
    if isinstance(data, dict):
        #检查当前字典是否有id键且值在排除列表中
        if 'id' in data and data['id'] in exclude_ids:
            return None  #返回None表示删除此对象
        
        #递归处理字典的每个值
        filtered = {}
        for key, value in data.items():
            filtered_value = filter_excluded_ids(value, exclude_ids)
            if filtered_value is not None:
                filtered[key] = filtered_value
        
        return filtered
    
    elif isinstance(data, list):
        #递归处理列表，过滤掉返回None的项
        filtered = []
        for item in data:
            filtered_item = filter_excluded_ids(item, exclude_ids)
            if filtered_item is not None:
                filtered.append(filtered_item)
        return filtered
    
    else:
        #其他类型直接返回
        return data


def detect_armor_set(data):
    """检测ArmorItems第一项的id，返回对应的装备套装描述"""
    if isinstance(data, dict) and 'ArmorItems' in data:
        armor_items = data['ArmorItems']
        if isinstance(armor_items, list) and len(armor_items) > 0:
            first_item = armor_items[0]
            if isinstance(first_item, dict) and 'id' in first_item:
                armor_id = first_item['id']
                # 根据id返回对应的描述
                armor_map = {
                    "minecraft:netherite_boots": "下界合金套",
                    "twilightforest:yeti_boots": "雪怪套",
                }
                return armor_map.get(armor_id, "")
    return ""


def sum_armor_enchantments(data):
    """提取ArmorItems下所有项目的enchantments，将相同键名的键值相加"""
    enchantment_sum = {}
    
    if isinstance(data, dict) and 'ArmorItems' in data:
        armor_items = data['ArmorItems']
        if isinstance(armor_items, list):
            for item in armor_items:
                if isinstance(item, dict) and 'components' in item:
                    components = item['components']
                    if isinstance(components, dict) and 'minecraft:enchantments' in components:
                        enchantments = components['minecraft:enchantments']
                        if isinstance(enchantments, dict):
                            # 检查是否有levels嵌套结构
                            if 'levels' in enchantments and isinstance(enchantments['levels'], dict):
                                enchant_levels = enchantments['levels']
                            else:
                                enchant_levels = enchantments
                            
                            # 遍历所有附魔键值对
                            for enchant_name, enchant_level in enchant_levels.items():
                                # 如果值是字典，尝试获取其数值
                                if isinstance(enchant_level, dict):
                                    # 如果是嵌套字典，尝试获取第一个数值
                                    continue
                                elif isinstance(enchant_level, (int, float)):
                                    if enchant_name in enchantment_sum:
                                        enchantment_sum[enchant_name] += enchant_level
                                    else:
                                        enchantment_sum[enchant_name] = enchant_level
    
    return enchantment_sum


def remove_armor_items_details(data):
    """删除ArmorItems中每个项目的详细信息，仅保留id（保留filter_drop_items过滤出的完整内容）"""
    if isinstance(data, dict) and 'ArmorItems' in data:
        armor_items = data['ArmorItems']
        if isinstance(armor_items, list):
            simplified_items = []
            for item in armor_items:
                if isinstance(item, dict) and 'id' in item:
                    # 检查是否只有id和components两个键（即filter_drop_items简化后的结构）
                    if set(item.keys()) == {'id', 'components'}:
                        # 这是被filter_drop_items简化过的（掉落概率==0），简化为仅保留id
                        simplified_items.append({'id': item['id']})
                    else:
                        # 这是filter_drop_items保留的完整内容（掉落概率!=0），保留原样
                        simplified_items.append(item)
                else:
                    simplified_items.append(item)
            data['ArmorItems'] = simplified_items
    
    return data


def convert_single_file(input_file, output_file, exclude_ids=None):
    """将单个NBT文件转换为JSON文件"""
    if exclude_ids is None:
        exclude_ids = EXCLUDE_IDS
    
    #读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        input_text = f.read()
    
    #创建转换器
    converter = NBTToJSONConverter()
    
    #提取entity_data
    nbt_text = converter.extract_entity_data(input_text)
    
    #解析NBT
    data = converter.parse_nbt(nbt_text)
    
    #计算属性修饰符
    data = calculate_attribute_modifiers(data)
    
    #过滤掉落物品
    data = filter_drop_items(data)
    
    #过滤排除的id
    if exclude_ids:
        data = filter_excluded_ids(data, exclude_ids)
    
    #应用数值区间计算实际值（在翻译之前生效）
    if VALUE_RANGES:
        data = apply_value_ranges(data, VALUE_RANGES)
    
    #翻译键名
    if KEY_TRANSLATION:
        data = translate_keys(data, KEY_TRANSLATION)
    
    #删除指定键名
    if REMOVE_KEYS:
        data = remove_keys(data, REMOVE_KEYS)
    
    #格式化CustomName
    data = format_custom_name(data)
    
    #检测装备套装并添加描述
    armor_desc = detect_armor_set(data)
    
    #计算附魔总和
    enchantment_sum = sum_armor_enchantments(data)
    
    #删除ArmorItems详细信息
    data = remove_armor_items_details(data)
    
    #写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        if armor_desc or enchantment_sum:
            # 在JSON数据中添加描述字段
            output_data = {}
            if armor_desc:
                output_data["_描述"] = armor_desc
            if enchantment_sum:
                output_data["_附魔总和"] = enchantment_sum
            if isinstance(data, dict):
                output_data.update(data)
            else:
                output_data["_数据"] = data
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"成功转换：{os.path.basename(input_file)} -> {os.path.basename(output_file)}")


def batch_convert(directory, output_dir=None, exclude_ids=None):
    """批量转换目录下所有以/开头的txt文件"""
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    
    if not txt_files:
        print(f"在目录{directory}中未找到任何txt文件")
        return
    
    #如果没有指定输出目录，使用input目录
    if output_dir is None:
        output_dir = directory
    
    #确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for txt_file in sorted(txt_files):
        try:
            #读取文件检查是否以/开头
            with open(txt_file, 'r', encoding='utf-8') as f:
                first_char = f.read(1)
            
            if first_char != '/':
                print(f"跳过：{os.path.basename(txt_file)}（不以/开头）")
                skip_count += 1
                continue
            
            #生成输出文件名（保存到output目录）
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}_convert.json")
            
            #转换文件
            convert_single_file(txt_file, output_file, exclude_ids)
            success_count += 1
            
        except Exception as e:
            print(f"错误处理{os.path.basename(txt_file)}：{e}")
            error_count += 1
    
    print(f"\n批量转换完成！成功：{success_count}，跳过：{skip_count}，错误：{error_count}")


if __name__ == "__main__":
    #默认处理脚本所在目录下input文件夹中的所有txt文件，输出到output文件夹
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    output_dir = os.path.join(script_dir, "output")
    
    if len(sys.argv) > 1:
        #如果提供了目录参数，使用该目录作为输入目录
        target_dir = sys.argv[1]
        #如果提供了第二个参数，使用该目录作为输出目录
        output_target = sys.argv[2] if len(sys.argv) > 2 else target_dir
    else:
        #否则使用input文件夹作为输入，output文件夹作为输出
        target_dir = input_dir
        output_target = output_dir
    
    try:
        batch_convert(target_dir, output_target)
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)