"""文本差异计算工具

用于计算两段文本之间的差异，支持实时文本输入的智能更新。
"""


def calculate_text_diff(old_text: str, new_text: str) -> tuple[int, str]:
    """计算文本差异（差量算法）

    找到两段文本的公共前缀，计算需要退格删除的字符数和需要追加的文本。
    这种算法适用于实时语音识别场景，其中新文本通常是旧文本的扩展或修正。

    Args:
        old_text: 旧文本（上一次输入的文本）
        new_text: 新文本（当前需要输入的文本）

    Returns:
        tuple[int, str]: (backspace_count, text_to_append)
            - backspace_count: 需要退格删除的字符数
            - text_to_append: 需要追加输入的文本

    Examples:
        >>> calculate_text_diff("你好", "你好世界")
        (0, "世界")

        >>> calculate_text_diff("你好", "你号")
        (1, "号")

        >>> calculate_text_diff("", "你好")
        (0, "你好")
    """
    # 处理空字符串情况
    if not old_text:
        return 0, new_text

    if not new_text:
        # 新文本为空，删除所有旧文本
        return len(old_text), ""

    # 找到公共前缀长度
    common_prefix_len = 0
    min_len = min(len(old_text), len(new_text))

    for i in range(min_len):
        if old_text[i] == new_text[i]:
            common_prefix_len = i + 1
        else:
            break

    # 需要删除的字符数 = 旧文本长度 - 公共前缀长度
    backspace_count = len(old_text) - common_prefix_len

    # 需要追加的文本 = 新文本从公共前缀之后的部分
    text_to_append = new_text[common_prefix_len:]

    return backspace_count, text_to_append
