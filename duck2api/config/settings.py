"""应用配置模块。

管理环境变量与全局运行时参数。
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局应用配置类。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 服务监听配置
    host: str = "0.0.0.0"
    port: int = 8080
    prefix: str = ""

    # API 认证（若配置则校验 Bearer Token）
    authorization: Optional[str] = None
    api_key: Optional[str] = None

    # 网络代理设置
    proxy_url: Optional[str] = None
    proxies_file: str = "proxies.txt"

    # Playwright 浏览器引擎配置
    duck_base_url: str = "https://duck.ai"
    browser_headless: bool = True
    browser_channel: Optional[str] = None
    browser_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/133.0.0.0 Safari/537.36"
    )
    browser_timeout_ms: int = 60000
    page_pool_size: int = 3
    page_idle_recycle_seconds: int = 600

    @property
    def effective_api_key(self) -> Optional[str]:
        """获取有效的鉴权密钥（去除 Bearer 前缀）。"""
        key = self.authorization or self.api_key
        if key and key.startswith("Bearer "):
            return key[7:].strip()
        return key.strip() if key else None


settings = Settings()