"""从模型回复中读取 JSON，兼容代码块和前后说明文字。"""

import json


def parse_json_response(content: str):
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(content):
            if char in "{[":
                try:
                    result, _ = decoder.raw_decode(content[index:])
                    return result
                except json.JSONDecodeError:
                    continue
    raise ValueError("回复中没有有效的 JSON 数据")
