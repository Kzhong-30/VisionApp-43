import random
from typing import Tuple

CATEGORIES = {
    "可回收物": ["塑料瓶", "易拉罐", "旧报纸", "纸箱", "玻璃瓶", "旧衣服", "金属餐具", "塑料玩具"],
    "有害垃圾": ["电池", "过期药品", "荧光灯管", "温度计", "油漆桶", "杀虫剂瓶", "水银血压计", "消毒剂瓶"],
    "厨余垃圾": ["剩菜剩饭", "果皮", "蛋壳", "茶叶渣", "鱼骨", "菜叶", "果皮核", "咖啡渣"],
    "其他垃圾": ["烟蒂", "陶瓷碎片", "用过的纸巾", "尿不湿", "一次性餐具", "灰土", "破旧陶瓷", "受污染纸张"],
}

DISPOSAL_GUIDES = {
    "可回收物": "请将可回收物清洁干燥后投放至蓝色可回收物桶内，注意去除包装物。",
    "有害垃圾": "请投放至红色有害垃圾桶内，易碎物品请包裹后投放，易挥发物品请密封后投放。",
    "厨余垃圾": "请投放至绿色厨余垃圾桶内，沥干水分，去除包装物后投放。",
    "其他垃圾": "请投放至灰色其他垃圾桶内。",
}

DISPOSAL_METHODS = {
    "可回收物": "回收利用",
    "有害垃圾": "专门无害化处理",
    "厨余垃圾": "堆肥/生化处理",
    "其他垃圾": "卫生填埋/焚烧",
}


def classify_image(image_bytes: bytes, filename: str) -> Tuple[str, float, str]:
    all_items = []
    for cat, items in CATEGORIES.items():
        for item in items:
            all_items.append((item, cat))
    
    item_name, category = random.choice(all_items)
    confidence = round(random.uniform(0.7, 0.99), 2)
    return category, confidence, item_name
