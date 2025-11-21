"""文本差异计算工具

用于计算两段文本之间的差异，支持实时文本输入的智能更新。
"""


def find_longest_common_substring(s1: str, s2: str) -> tuple[int, int, int]:
    """查找两个字符串的最长公共子串

    Args:
        s1: 第一个字符串
        s2: 第二个字符串

    Returns:
        tuple[int, int, int]: (start_in_s1, start_in_s2, length)
            - start_in_s1: 公共子串在s1中的起始位置
            - start_in_s2: 公共子串在s2中的起始位置
            - length: 公共子串的长度
    """
    if not s1 or not s2:
        return 0, 0, 0

    m, n = len(s1), len(s2)
    # dp[i][j] 表示以s1[i-1]和s2[j-1]结尾的最长公共子串长度
    max_len = 0
    end_pos_s1 = 0
    end_pos_s2 = 0

    # 使用滚动数组优化空间复杂度
    prev_row = [0] * (n + 1)

    for i in range(1, m + 1):
        curr_row = [0] * (n + 1)
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                curr_row[j] = prev_row[j - 1] + 1
                if curr_row[j] > max_len:
                    max_len = curr_row[j]
                    end_pos_s1 = i
                    end_pos_s2 = j
        prev_row = curr_row

    if max_len == 0:
        return 0, 0, 0

    return end_pos_s1 - max_len, end_pos_s2 - max_len, max_len


def calculate_text_diff(old_text: str, new_text: str) -> tuple[int, str]:
    """计算文本差异（改进的差量算法）

    使用最长公共子串算法来处理实时语音识别中的文本修正。
    当sherpa-onnx修正之前的识别结果时,算法能够找到公共部分并正确应用修正。

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

        >>> calculate_text_diff("从这个层面上来说便宜", "那制的从这个层面上来说便")
        (4, "那制的")
    """
    # 处理空字符串情况
    if not old_text:
        return 0, new_text

    if not new_text:
        # 新文本为空，删除所有旧文本
        return len(old_text), ""

    # 策略1: 先尝试简单的前缀匹配(最常见的情况:追加)
    common_prefix_len = 0
    min_len = min(len(old_text), len(new_text))

    for i in range(min_len):
        if old_text[i] == new_text[i]:
            common_prefix_len = i + 1
        else:
            break

    # 如果找到了较长的公共前缀(超过50%),使用简单算法
    if common_prefix_len >= min_len * 0.5:
        backspace_count = len(old_text) - common_prefix_len
        text_to_append = new_text[common_prefix_len:]
        return backspace_count, text_to_append

    # 策略2: 前缀匹配失败,使用最长公共子串算法
    start_old, start_new, lcs_len = find_longest_common_substring(old_text, new_text)

    # 如果没有找到足够长的公共子串,使用完全重写策略
    min_lcs_threshold = min(5, min_len // 3)  # 至少5个字符或1/3长度
    if lcs_len < min_lcs_threshold:
        # 完全重写:删除所有旧文本,输入所有新文本
        return len(old_text), new_text

    # 找到了公共子串,计算差异
    # 需要删除的是:从当前光标位置(old_text末尾)到公共子串结束位置
    # 即:删除 old_text[start_old + lcs_len:] 的内容
    backspace_count = len(old_text) - (start_old + lcs_len)

    # 需要追加的是:公共子串之前的new_text部分 + 公共子串之后的new_text部分
    # 即:new_text[:start_new] + new_text[start_new + lcs_len:]
    text_before_lcs = new_text[:start_new]
    text_after_lcs = new_text[start_new + lcs_len :]
    text_to_append = text_before_lcs + text_after_lcs

    return backspace_count, text_to_append
