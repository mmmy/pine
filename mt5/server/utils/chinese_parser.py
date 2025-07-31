"""
Chinese message parser for MT5 Trading HTTP Server.
Parses Chinese text commands into trading parameters.
"""

import re
from typing import Dict, Any, Optional, List
from utils.exceptions import ValidationError


class ChineseMessageParser:
    """Parser for Chinese trading messages."""
    
    # 操作方向映射
    ACTION_MAP = {
        '开多': 'buy',
        '买入': 'buy',
        '做多': 'buy',
        '开空': 'sell',
        '卖出': 'sell',
        '做空': 'sell',
        '平多': 'close_long',
        '平空': 'close_short',
        '平仓': 'close',
        '全平': 'close_all',
        '修改': 'modify'
    }
    
    # 参数映射
    PARAM_MAP = {
        '仓位': 'volume',
        '数量': 'volume',
        '手数': 'volume',
        '止损': 'sl',
        '止损价': 'sl',
        '止损价格': 'sl',
        '止盈': 'tp',
        '止盈价': 'tp',
        '止盈价格': 'tp',
        '价格': 'price',
        '开仓价': 'price',
        '开仓价格': 'price',
        '备注': 'comment',
        '注释': 'comment',
        '说明': 'comment',
        '魔术数': 'magic',
        '魔术数字': 'magic',
        '订单号': 'ticket',
        '票号': 'ticket',
        '持仓号': 'ticket',
        '滑点': 'deviation',
        '最大滑点': 'deviation'
        # 移除账户相关参数，现在只使用当前登录的MT5账户
    }
    
    # 开关参数
    SWITCH_PARAMS = {
        '允许滑点': 'allow_slippage',
        '强制平仓': 'force_close',
        '部分平仓': 'partial_close',
        '立即执行': 'immediate',
        '市价单': 'market_order',
        '限价单': 'limit_order',
        '开启时间区间': 'enable_time_check'
    }
    
    def __init__(self):
        """Initialize parser."""
        pass
    
    def parse_message(self, message: str) -> Dict[str, Any]:
        """
        Parse Chinese message into trading parameters.
        
        Args:
            message: Chinese trading message
            
        Returns:
            Dictionary with trading parameters
            
        Raises:
            ValidationError: If message format is invalid
        """
        if not message or not isinstance(message, str):
            raise ValidationError("消息不能为空")
        
        # 清理消息
        message = message.strip()
        if not message:
            raise ValidationError("消息内容为空")
        
        # 分割消息为词组
        parts = self._split_message(message)
        if len(parts) < 1:
            raise ValidationError("消息格式错误，至少需要操作方向")

        # 检查是否包含"开启时间区间"开关参数
        enable_time_check = False
        if "开启时间区间" in parts:
            enable_time_check = True
            parts.remove("开启时间区间")  # 移除开关参数，继续解析其他部分

        if len(parts) < 1:
            raise ValidationError("消息格式错误，至少需要操作方向")

        # 解析操作方向
        action_text = parts[0]
        action = self._parse_action(action_text)

        # 构建基础参数
        params = {
            'action': action
        }

        # 如果启用了时间检查，添加到参数中
        if enable_time_check:
            params['enable_time_check'] = True

        # 普通交易命令，需要交易品种
        if len(parts) < 2:
            raise ValidationError(f"缺少交易品种 (action={action}, parts={len(parts)})")

        # 解析交易品种
        symbol = parts[1].upper()
        if not self._is_valid_symbol(symbol):
            raise ValidationError(f"无效的交易品种: {symbol}")

        params['symbol'] = symbol
        start_index = 2
        
        # 解析其他参数
        for i in range(start_index, len(parts)):
            part = parts[i]
            self._parse_parameter(part, params)
        
        return params
    
    def _split_message(self, message: str) -> List[str]:
        """Split message into parts."""
        # 先检查是否以多词操作开头
        multi_word_actions = ['开启时间区间']

        for action in multi_word_actions:
            if message.startswith(action):
                # 找到多词操作，分割剩余部分
                remaining = message[len(action):].strip()
                if remaining:
                    # 分割剩余参数
                    remaining_parts = []
                    current_part = ""

                    for char in remaining:
                        if char == ' ':
                            if current_part:
                                remaining_parts.append(current_part)
                                current_part = ""
                        else:
                            current_part += char

                    if current_part:
                        remaining_parts.append(current_part)

                    return [action] + remaining_parts
                else:
                    return [action]

        # 普通分割逻辑
        parts = []
        current_part = ""

        for char in message:
            if char == ' ':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char

        if current_part:
            parts.append(current_part)

        return parts
    
    def _parse_action(self, action_text: str) -> str:
        """Parse action from Chinese text."""
        action = self.ACTION_MAP.get(action_text)
        if not action:
            raise ValidationError(f"不支持的操作方向: {action_text}")
        return action
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol format is valid."""
        # 基本的交易品种格式检查
        if not symbol:
            return False
        
        # 允许字母、数字、点、斜杠、下划线
        pattern = r'^[A-Z0-9._/]+$'
        return bool(re.match(pattern, symbol))
    
    def _parse_parameter(self, part: str, params: Dict[str, Any]) -> None:
        """Parse a parameter part."""
        if '=' in part:
            # 键值对参数
            key, value = part.split('=', 1)
            self._parse_key_value(key, value, params)
        else:
            # 开关参数
            self._parse_switch(part, params)
    
    def _parse_key_value(self, key: str, value: str, params: Dict[str, Any]) -> None:
        """Parse key-value parameter."""
        # 映射中文键名
        param_name = self.PARAM_MAP.get(key)
        if not param_name:
            # 如果不在映射中，使用原始键名（转换为小写）
            param_name = key.lower()
        
        # 转换值的类型
        converted_value = self._convert_value(param_name, value)
        params[param_name] = converted_value
    
    def _parse_switch(self, switch: str, params: Dict[str, Any]) -> None:
        """Parse switch parameter."""
        param_name = self.SWITCH_PARAMS.get(switch)
        if param_name:
            params[param_name] = True
        else:
            # 未知开关，记录为自定义参数
            params[f"switch_{switch}"] = True
    
    def _convert_value(self, param_name: str, value: str) -> Any:
        """Convert value to appropriate type."""
        if not value:
            return None
        
        # 数值类型参数
        numeric_params = ['volume', 'sl', 'tp', 'price', 'deviation', 'magic', 'ticket']
        
        if param_name in numeric_params:
            try:
                # 尝试转换为浮点数
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                raise ValidationError(f"参数 {param_name} 的值 '{value}' 不是有效数字")
        
        # 字符串类型参数
        return value
    
    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parsed parameters."""
        action = params.get('action')
        symbol = params.get('symbol')

        if not action:
            raise ValidationError("缺少操作方向")

        if not symbol:
            raise ValidationError("缺少交易品种")
        
        # 根据操作类型验证必需参数
        if action in ['buy', 'sell']:
            # 开仓操作，检查仓位
            volume = params.get('volume')
            if volume is not None and volume <= 0:
                raise ValidationError("仓位必须大于0")
        
        elif action in ['close_long', 'close_short', 'close']:
            # 平仓操作的特殊处理
            pass
        
        elif action == 'modify':
            # 修改操作需要订单号
            if 'ticket' not in params:
                raise ValidationError("修改操作需要指定订单号")
    
    def convert_to_standard_format(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parsed parameters to standard webhook format."""
        standard_params = {}
        
        # 处理特殊的操作类型
        action = params['action']
        if action == 'close_long':
            standard_params['action'] = 'close'
            standard_params['close_type'] = 'long'
        elif action == 'close_short':
            standard_params['action'] = 'close'
            standard_params['close_type'] = 'short'
        else:
            standard_params['action'] = action
        
        # 复制其他标准参数
        standard_fields = ['symbol', 'volume', 'sl', 'tp', 'price', 'comment', 'magic', 'ticket']

        # 复制标准字段
        for field in standard_fields:
            if field in params:
                standard_params[field] = params[field]
        
        # 处理开关参数
        if params.get('allow_slippage'):
            standard_params['deviation'] = params.get('deviation', 10)

        # 处理时间区间检查参数
        if params.get('enable_time_check'):
            standard_params['enable_time_check'] = True
        
        return standard_params


def parse_chinese_message(message: str) -> Dict[str, Any]:
    """
    Convenience function to parse Chinese message.
    
    Args:
        message: Chinese trading message
        
    Returns:
        Standard webhook parameters
    """
    parser = ChineseMessageParser()
    params = parser.parse_message(message)
    parser.validate_params(params)
    return parser.convert_to_standard_format(params)
