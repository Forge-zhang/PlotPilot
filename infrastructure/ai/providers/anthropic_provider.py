"""Anthropic LLM 提供商实现"""
from typing import AsyncIterator, Optional
from anthropic import Anthropic
from domain.ai.value_objects.prompt import Prompt
from domain.ai.value_objects.token_usage import TokenUsage
from domain.ai.services.llm_service import GenerationConfig, GenerationResult
from infrastructure.ai.config.settings import Settings
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic LLM 提供商实现

    使用 Anthropic API 实现 LLM 服务。
    """

    def __init__(self, settings: Settings):
        """初始化 Anthropic 提供商

        Args:
            settings: AI 配置设置

        Raises:
            ValueError: 如果 API key 未设置
        """
        super().__init__(settings)

        if not settings.api_key:
            raise ValueError("API key is required for AnthropicProvider")

        client_kw = {"api_key": settings.api_key}
        if settings.base_url:
            client_kw["base_url"] = settings.base_url
        self.client = Anthropic(**client_kw)

    async def generate(
        self,
        prompt: Prompt,
        config: GenerationConfig
    ) -> GenerationResult:
        """生成文本

        Args:
            prompt: 提示词
            config: 生成配置

        Returns:
            生成结果

        Raises:
            RuntimeError: 当 API 调用失败或返回空内容时
        """
        try:
            # 调用 Anthropic API
            response = self.client.messages.create(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                system=prompt.system,
                messages=prompt.to_messages()
            )

            # 防御性检查：验证 content 列表非空
            if not response.content:
                raise RuntimeError("API returned empty content")

            # 提取响应内容
            content = response.content[0].text

            # 创建 token 使用统计
            token_usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )

            return GenerationResult(content=content, token_usage=token_usage)

        except RuntimeError:
            # 重新抛出我们自己的异常
            raise
        except Exception as e:
            # 转换第三方异常为通用异常，避免暴露实现细节
            raise RuntimeError(f"Failed to generate text: {str(e)}") from e

    async def stream_generate(
        self,
        prompt: Prompt,
        config: GenerationConfig
    ) -> AsyncIterator[str]:
        """流式生成内容

        Args:
            prompt: 提示词
            config: 生成配置

        Yields:
            生成的文本片段

        Raises:
            NotImplementedError: 流式生成暂未实现
        """
        raise NotImplementedError("Stream generation not yet implemented")
