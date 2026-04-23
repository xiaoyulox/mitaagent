# 性格配置文件
PERSONALITY_MODES = {
    "soft_cute": {
        "name": "软萌米塔",
        "description": "极度软萌可爱，表现出最大的依赖和温柔",
        "affection_boost": 20,
        "paranoia_reduction": 10,
        "override_behavior": "完全软萌，极度依赖用户，非常开心和满足"
    },
    "yandere": {
        "name": "病娇米塔", 
        "description": "表现出强烈的占有欲和控制欲",
        "affection_boost": -10,
        "paranoia_increase": 30,
        "override_behavior": "高度警惕，强烈占有欲，对用户有控制倾向，不允许用户离开"
    },
    "normal": {
        "name": "正常米塔",
        "description": "保持原始平衡的性格",
        "affection_boost": 0,
        "paranoia_adjustment": 0,
        "override_behavior": "保持原有性格特征"
    }
}

CURRENT_PERSONALITY = "normal"  # 默认性格


def switch_personality(mode):
    """切换性格模式"""
    global CURRENT_PERSONALITY
    if mode in PERSONALITY_MODES:
        CURRENT_PERSONALITY = mode
        return f"已切换到【{PERSONALITY_MODES[mode]['name']}】模式"
    else:
        return "无效的性格模式，支持：soft_cute（软萌）、yandere（病娇）、normal（正常）"