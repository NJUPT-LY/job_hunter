"""
职路AI - 结构化日志配置模块

功能:
- 支持文本和JSON两种日志格式
- 区分开发环境(DEBUG)和生产环境(INFO)日志级别
- 日志轮转: 按天分割, 保留指定天数(默认30天)
- 同时输出到控制台和文件
"""

import logging
import json
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


class JSONFormatter(logging.Formatter):
    """
    JSON格式日志格式化器
    输出结构化的JSON日志, 便于生产环境日志采集和分析
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # 添加异常信息
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        return json.dumps(log_entry, ensure_ascii=False)


class RequestIdFilter(logging.Filter):
    """
    日志过滤器: 为每条日志添加请求ID(如果存在)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return True


def get_log_level(env: str, config_level: Optional[str] = None) -> int:
    """
    根据环境和配置返回日志级别

    Args:
        env: 运行环境 (development/production)
        config_level: 配置文件中的日志级别

    Returns:
        logging level constant
    """
    if config_level:
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        return level_map.get(config_level.upper(), logging.INFO)

    # 默认行为: 开发环境DEBUG, 生产环境INFO
    if env.lower() == "production":
        return logging.INFO
    return logging.DEBUG


def setup_logging(
    env: str = "development",
    log_level: Optional[str] = None,
    log_format: str = "text",
    log_dir: str = "./logs",
    rotation_days: int = 30,
) -> None:
    """
    配置全局日志系统

    Args:
        env: 运行环境 (development/production)
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_format: 日志格式 (text/json)
        log_dir: 日志文件目录
        rotation_days: 日志保留天数
    """
    level = get_log_level(env, log_level)

    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除已有handler避免重复
    root_logger.handlers.clear()

    # 添加请求ID过滤器
    request_id_filter = RequestIdFilter()

    # === 控制台Handler ===
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    if log_format == "json":
        console_formatter = JSONFormatter()
    else:
        # 开发环境使用可读性更好的文本格式
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(request_id_filter)
    root_logger.addHandler(console_handler)

    # === 文件Handler (按天轮转) ===
    log_file = os.path.join(log_dir, "zhilu.log")

    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",  # 每天午夜分割
        interval=1,
        backupCount=rotation_days,  # 保留指定天数
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.suffix = "%Y-%m-%d.log"  # 轮转文件名后缀

    if log_format == "json":
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(request_id_filter)
    root_logger.addHandler(file_handler)

    # === 错误日志单独文件 ===
    error_file = os.path.join(log_dir, "zhilu_error.log")
    error_handler = TimedRotatingFileHandler(
        filename=error_file,
        when="midnight",
        interval=1,
        backupCount=rotation_days,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        JSONFormatter() if log_format == "json" else file_formatter
    )
    error_handler.addFilter(request_id_filter)
    root_logger.addHandler(error_handler)

    logging.info(
        "日志系统初始化完成 - 环境: %s, 级别: %s, 格式: %s, 轮转保留: %d天",
        env,
        logging.getLevelName(level),
        log_format,
        rotation_days,
    )
