#!/usr/bin/env python3
"""
Test time interval parser.
"""

from utils.chinese_parser import parse_chinese_message


def test_time_commands():
    """Test time interval commands."""
    
    test_messages = [
        "开启时间区间 开始时间=09:00 结束时间=17:00 时区=UTC",
        "关闭时间区间",
        "设置时间区间 开始时间=22:00 结束时间=06:00"
    ]
    
    for message in test_messages:
        print(f"\n测试消息: {message}")
        try:
            # 先测试分割
            from utils.chinese_parser import ChineseMessageParser
            parser = ChineseMessageParser()
            parts = parser._split_message(message)
            print(f"分割结果: {parts}")

            # 测试action解析
            if parts:
                action_text = parts[0]
                try:
                    action = parser._parse_action(action_text)
                    print(f"解析的action: {action}")
                except Exception as e:
                    print(f"Action解析错误: {e}")

            # 然后测试完整解析
            try:
                result = parse_chinese_message(message)
                print(f"完整解析结果: {result}")
            except Exception as e:
                print(f"完整解析错误: {e}")
        except Exception as e:
            print(f"解析错误: {e}")


if __name__ == '__main__':
    test_time_commands()
