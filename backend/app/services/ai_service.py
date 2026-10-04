"""
AI服务统一接口层 - 支持多提供商与自动降级

功能：
- 统一AI调用接口：chat_completion(prompt, system_prompt)
- 多提供商支持：OpenAI / DashScope(通义千问) / Zhipu(智谱AI)
- 配置驱动，从.env读取API配置
- API不可用时自动降级到规则引擎
- 完整的调用日志与错误处理
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from openai import AsyncOpenAI, APIError, APITimeoutError, AuthenticationError, APIConnectionError

from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 各提供商的API Base URL预设
PROVIDER_BASE_URLS: Dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
}

# 各提供商的默认模型
DEFAULT_MODELS: Dict[str, str] = {
    "openai": "gpt-3.5-turbo",
    "dashscope": "qwen-turbo",
    "zhipu": "glm-4-flash",
}

# 调用超时设置（秒）
AI_TIMEOUT = settings.AI_TIMEOUT


@dataclass
class AILogEntry:
    """AI调用日志条目"""
    timestamp: float = 0.0
    provider: str = ""
    model: str = ""
    prompt_length: int = 0
    status: str = ""  # success / failed / fallback
    error_message: str = ""
    duration_ms: float = 0.0
    is_fallback: bool = False

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "prompt_length": self.prompt_length,
            "status": self.status,
            "error_message": self.error_message,
            "duration_ms": round(self.duration_ms, 2),
            "is_fallback": self.is_fallback,
        }


# 调用日志历史（内存存储，最近的调用记录）
_call_log: list = []
_max_log_entries = 100


def _add_log_entry(entry: AILogEntry) -> None:
    """添加日志条目到历史记录"""
    _call_log.append(entry)
    if len(_call_log) > _max_log_entries:
        _call_log.pop(0)


def get_call_log() -> list:
    """获取AI调用日志"""
    return [entry.to_dict() for entry in _call_log]


def get_provider_config() -> Dict[str, str]:
    """获取当前AI提供商配置"""
    provider = settings.AI_PROVIDER.lower()
    base_url = settings.AI_API_BASE_URL or PROVIDER_BASE_URLS.get(provider)
    model = settings.AI_MODEL or DEFAULT_MODELS.get(provider)

    return {
        "provider": provider,
        "api_key": settings.AI_API_KEY,
        "base_url": base_url,
        "model": model,
    }


def is_api_key_configured(api_key: Optional[str]) -> bool:
    if not api_key or not api_key.strip():
        return False
    value = api_key.strip().lower()
    return not any(marker in value for marker in ("your", "example", "placeholder", "sk-xxx"))


async def chat_completion(
    prompt: str,
    system_prompt: str = "你是一个专业的助手。",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> Dict[str, Any]:
    """
    统一的AI聊天补全接口

    参数:
        prompt: 用户输入的提示词
        system_prompt: 系统提示词
        temperature: 生成温度 (0.0-1.0)
        max_tokens: 最大生成token数

    返回:
        {
            "content": str,           # AI回复内容
            "provider": str,          # 使用的提供商
            "model": str,             # 使用的模型
            "is_fallback": bool,      # 是否使用了降级方案
            "status": str,            # success / failed
            "error_message": str,     # 错误信息（如有）
            "duration_ms": float,     # 耗时（毫秒）
        }
    """
    config = get_provider_config()
    provider = config["provider"]
    api_key = config["api_key"]
    base_url = config["base_url"]
    model = config["model"]

    log_entry = AILogEntry(
        timestamp=time.time(),
        provider=provider,
        model=model,
        prompt_length=len(prompt),
    )

    start_time = time.time()

    # 检查API Key是否配置
    if not is_api_key_configured(api_key):
        logger.warning("AI API Key未配置，自动降级到规则引擎")
        return _fallback_to_rule_engine(prompt, system_prompt, log_entry)

    # 尝试调用AI API
    try:
        async with AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=settings.AI_TIMEOUT,
            max_retries=0,
        ) as client:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

        duration_ms = (time.time() - start_time) * 1000
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise ValueError("模型回复为空")

        log_entry.duration_ms = duration_ms
        log_entry.status = "success"
        _add_log_entry(log_entry)

        logger.info(
            f"AI调用成功 | 提供商: {provider} | 模型: {model} | "
            f"耗时: {duration_ms:.0f}ms | 响应长度: {len(content)}字符"
        )

        return {
            "content": content,
            "provider": provider,
            "model": model,
            "is_fallback": False,
            "status": "success",
            "error_message": "",
            "duration_ms": round(duration_ms, 2),
        }

    except AuthenticationError as e:
        error_msg = f"API Key无效或认证失败: {str(e)}"
        logger.error(error_msg)
    except APITimeoutError as e:
        error_msg = f"AI请求超时（{settings.AI_TIMEOUT}秒）: {str(e)}"
        logger.error(error_msg)
    except APIConnectionError as e:
        error_msg = f"无法连接到AI服务: {str(e)}"
        logger.error(error_msg)
    except APIError as e:
        error_msg = f"AI API请求失败 (状态码: {e.status_code}): {str(e)}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"AI调用发生未知错误: {str(e)}"
        logger.error(error_msg)

    # 所有异常都降级到规则引擎
    duration_ms = (time.time() - start_time) * 1000
    log_entry.duration_ms = duration_ms
    log_entry.status = "fallback"
    log_entry.error_message = error_msg
    log_entry.is_fallback = True
    logger.warning(f"AI调用失败，自动降级到规则引擎: {error_msg}")

    return _fallback_to_rule_engine(
        prompt, system_prompt, log_entry, fallback_reason=error_msg
    )


def _fallback_to_rule_engine(
    prompt: str,
    system_prompt: str,
    log_entry: AILogEntry,
    fallback_reason: str = "",
) -> Dict[str, Any]:
    """
    降级到规则引擎

    根据提示词内容，智能路由到现有的规则引擎方法
    """
    start_time = time.time()
    result = _route_to_analyzer(prompt)

    duration_ms = (time.time() - start_time) * 1000
    log_entry.duration_ms += duration_ms
    log_entry.error_message = fallback_reason
    log_entry.status = "fallback"
    log_entry.provider = "rule_engine"
    log_entry.model = "rule_engine"
    log_entry.is_fallback = True
    _add_log_entry(log_entry)

    return {
        "content": result,
        "provider": "rule_engine",
        "model": "rule_engine",
        "is_fallback": True,
        "status": "success",
        "error_message": f"AI服务不可用，已自动降级到规则引擎{': ' + fallback_reason if fallback_reason else ''}",
        "duration_ms": round(duration_ms, 2),
    }


def _route_to_analyzer(prompt: str) -> str:
    """
    根据提示词内容智能路由到对应的规则引擎方法
    """
    prompt_lower = prompt.lower()

    # 职位分析相关
    if any(kw in prompt_lower for kw in ["分析职位", "job analysis", "职位要求", "技能分析"]):
        return _analyze_job_by_rules(prompt)

    # JD解析相关
    if any(kw in prompt_lower for kw in ["解析", "parse", "jd", "job description", "职位描述"]):
        return _parse_jd_by_rules(prompt)

    # 面试评估相关
    if any(kw in prompt_lower for kw in ["面试", "interview", "评估回答", "evaluate"]):
        return _evaluate_interview_by_rules(prompt)

    # 行动规划相关
    if any(kw in prompt_lower for kw in ["行动计划", "action plan", "学习路线", "职业规划"]):
        return _generate_action_plan_by_rules(prompt)

    # 简历优化相关
    if any(kw in prompt_lower for kw in ["简历", "resume", "优化简历"]):
        return _optimize_resume_by_rules(prompt)

    # 默认：通用规则引擎回复
    return _generic_rule_response(prompt)


def _analyze_job_by_rules(prompt: str) -> str:
    """使用规则引擎进行职位分析"""
    return (
        "【规则引擎分析结果】\n\n"
        "基于关键词匹配和规则分析：\n"
        "1. 硬技能：通过职位描述中的技术关键词提取\n"
        "2. 软技能：识别沟通、协作、管理等关键词\n"
        "3. 经验要求：根据年限关键词判断职级\n"
        "4. 学历要求：根据教育关键词判断\n\n"
        "建议使用JobAnalyzer.analyze_job()进行深度分析。"
    )


def _parse_jd_by_rules(prompt: str) -> str:
    """使用规则引擎解析JD"""
    return (
        "【规则引擎JD解析】\n\n"
        "基于文本分析的职位描述解析：\n"
        "- 职责：提取包含'负责'、'参与'等关键词的句子\n"
        "- 技能：匹配预定义的技术技能词库\n"
        "- 经验：根据年限关键词判断\n"
        "- 学历：根据教育关键词判断"
    )


def _evaluate_interview_by_rules(prompt: str) -> str:
    """使用规则引擎评估面试回答"""
    return (
        "【规则引擎面试评估】\n\n"
        "基于关键词和长度的评估：\n"
        "- 回答长度充足：+10分\n"
        "- 结构清晰有条理：+5分\n"
        "- 结合实际经验：+10分\n"
        "- 缺少总结性陈述：-5分\n\n"
        "建议使用STAR法则组织回答。"
    )


def _generate_action_plan_by_rules(prompt: str) -> str:
    """使用规则引擎生成行动计划"""
    return (
        "【规则引擎行动计划】\n\n"
        "基于职位分类的模板化行动计划：\n"
        "阶段1：基础知识巩固\n"
        "阶段2：核心技能提升\n"
        "阶段3：项目实践\n"
        "阶段4：作品集准备\n"
        "阶段5：面试冲刺\n\n"
        "根据职位类型（技术/产品/数据分析）选择对应模板。"
    )


def _optimize_resume_by_rules(prompt: str) -> str:
    """使用规则引擎优化简历"""
    return (
        "【规则引擎简历优化】\n\n"
        "简历优化建议：\n"
        "1. 使用STAR法则描述经历\n"
        "2. 量化工作成果\n"
        "3. 突出与目标岗位匹配的技能\n"
        "4. 保持简洁，控制在一页内\n"
        "5. 避免拼写和语法错误"
    )


def _generic_rule_response(prompt: str) -> str:
    """通用规则引擎回复"""
    return (
        "【规则引擎回复】\n\n"
        f"收到您的请求：{prompt[:100]}...\n\n"
        "当前AI服务不可用，已自动降级到规则引擎模式。\n"
        "规则引擎基于预定义的关键词匹配和模板提供基础服务。\n"
        "配置AI API Key后可获得更智能的AI回复。"
    )


async def health_check() -> Dict[str, Any]:
    """
    AI服务健康检查

    返回当前AI服务的配置状态和可用性
    """
    config = get_provider_config()
    api_key_configured = is_api_key_configured(config["api_key"])

    result = {
        "provider": config["provider"],
        "base_url": config["base_url"],
        "model": config["model"],
        "api_key_configured": api_key_configured,
        "fallback_enabled": True,
        "timeout_seconds": settings.AI_TIMEOUT,
    }

    # 如果API Key已配置，尝试实际连接
    if api_key_configured:
        try:
            async with AsyncOpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
                timeout=10,
                max_retries=0,
            ) as client:
                await client.models.list()
            result["api_status"] = "connected"
            result["api_message"] = "AI服务连接正常"
        except AuthenticationError:
            result["api_status"] = "auth_failed"
            result["api_message"] = "API Key无效"
        except Exception as e:
            result["api_status"] = "connection_failed"
            result["api_message"] = f"连接失败: {str(e)}"
    else:
        result["api_status"] = "not_configured"
        result["api_message"] = "AI API Key未配置，将使用规则引擎降级方案"

    return result
