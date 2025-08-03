"""
Ollama客户端服务模块
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

import ollama
from loguru import logger


@dataclass
class ModelResponse:
    """模型响应数据类"""
    content: str
    model: str
    prompt: str
    response_time: float
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class PromptTemplate:
    """提示词模板数据类"""
    name: str
    template: str
    description: str
    variables: List[str]
    category: str = "general"


class OllamaClientError(Exception):
    """Ollama客户端错误"""
    pass


class OllamaClient:
    """Ollama客户端"""

    def __init__(self,
                 model: str = "qwen3:4b",
                 base_url: str = "http://localhost:11434",
                 timeout: int = 300,
                 prompts_dir: str = "config/prompts"):
        """
        初始化Ollama客户端

        Args:
            model: 使用的模型名称
            base_url: Ollama服务地址
            timeout: 请求超时时间（秒）
            prompts_dir: 提示词模板目录
        """
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.prompts_dir = Path(prompts_dir)

        # 提示词模板缓存
        self.prompt_templates: Dict[str, PromptTemplate] = {}

        # 默认生成参数
        self.default_options = {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1,
            'num_predict': 2048
        }

        logger.info(f"Ollama客户端初始化完成")
        logger.info(f"模型: {self.model}")
        logger.info(f"服务地址: {self.base_url}")
        logger.info(f"超时时间: {self.timeout}秒")

        # 加载提示词模板
        self._load_prompt_templates()

    def _load_prompt_templates(self):
        """加载提示词模板"""
        if not self.prompts_dir.exists():
            logger.warning(f"提示词目录不存在: {self.prompts_dir}")
            return

        logger.info(f"加载提示词模板: {self.prompts_dir}")

        template_files = list(self.prompts_dir.glob("*.txt"))

        for template_file in template_files:
            try:
                template = self._parse_template_file(template_file)
                self.prompt_templates[template.name] = template
                logger.debug(f"加载模板: {template.name}")
            except Exception as e:
                logger.error(f"加载模板失败 {template_file}: {e}")

        logger.info(f"已加载 {len(self.prompt_templates)} 个提示词模板")

    def _parse_template_file(self, template_file: Path) -> PromptTemplate:
        """解析提示词模板文件"""
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取模板变量
        import re
        # 只匹配简单的变量名（字母、数字、下划线）
        variables = re.findall(r'\{(\w+)\}', content)
        # 去重
        variables = list(set(variables))

        # 从文件名推断模板名称和类别
        name = template_file.stem
        category = "general"

        # 根据文件名推断类别
        if "entity" in name or "extraction" in name:
            category = "extraction"
        elif "query" in name:
            category = "query"
        elif "summary" in name:
            category = "summary"

        return PromptTemplate(
            name=name,
            template=content,
            description=f"从文件 {template_file.name} 加载的模板",
            variables=list(set(variables)),
            category=category
        )

    def test_connection(self) -> bool:
        """测试Ollama连接"""
        try:
            logger.info("测试Ollama连接...")

            # 获取模型列表
            models = ollama.list()
            model_list = getattr(models, 'models', [])
            logger.info(f"连接成功，可用模型数量: {len(model_list)}")

            # 检查指定模型是否可用
            available_models = []
            for m in model_list:
                if hasattr(m, 'model'):
                    available_models.append(m.model)
                elif isinstance(m, dict) and 'name' in m:
                    available_models.append(m['name'])
                elif isinstance(m, str):
                    available_models.append(m)

            if self.model not in available_models:
                logger.warning(f"指定模型 {self.model} 不在可用模型列表中")
                logger.info(f"可用模型: {available_models}")
                return False

            # 测试简单生成
            test_response = self.generate(
                prompt="Hello",
                options={'num_predict': 10}
            )

            if test_response.success:
                logger.info("✅ Ollama连接测试成功")
                return True
            else:
                logger.error(f"❌ 测试生成失败: {test_response.error_message}")
                return False

        except Exception as e:
            logger.error(f"❌ Ollama连接测试失败: {e}")
            return False

    def generate(self,
                 prompt: str,
                 model: Optional[str] = None,
                 options: Optional[Dict[str, Any]] = None,
                 stream: bool = False) -> ModelResponse:
        """
        生成文本

        Args:
            prompt: 输入提示词
            model: 使用的模型（可选，默认使用初始化时的模型）
            options: 生成参数（可选）
            stream: 是否流式生成

        Returns:
            ModelResponse: 生成结果
        """
        model = model or self.model
        options = {**self.default_options, **(options or {})}

        logger.debug(f"生成请求 - 模型: {model}, 提示词长度: {len(prompt)}")

        start_time = time.time()

        try:
            response = ollama.generate(
                model=model,
                prompt=prompt,
                options=options,
                stream=stream
            )

            end_time = time.time()
            response_time = end_time - start_time

            if stream:
                # 处理流式响应
                content = ""
                for chunk in response:
                    if 'response' in chunk:
                        content += chunk['response']

                response_content = content
            else:
                response_content = response.get('response', '')

            logger.debug(f"生成完成 - 响应时间: {response_time:.2f}秒, 响应长度: {len(response_content)}")

            return ModelResponse(
                content=response_content,
                model=model,
                prompt=prompt,
                response_time=response_time,
                success=True,
                metadata={
                    'options': options,
                    'stream': stream,
                    'prompt_tokens': len(prompt.split()),
                    'response_tokens': len(response_content.split())
                }
            )

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            logger.error(f"生成失败: {e}")

            return ModelResponse(
                content="",
                model=model,
                prompt=prompt,
                response_time=response_time,
                success=False,
                error_message=str(e)
            )

    def generate_with_template(self,
                              template_name: str,
                              variables: Dict[str, Any],
                              model: Optional[str] = None,
                              options: Optional[Dict[str, Any]] = None) -> ModelResponse:
        """
        使用模板生成文本

        Args:
            template_name: 模板名称
            variables: 模板变量
            model: 使用的模型
            options: 生成参数

        Returns:
            ModelResponse: 生成结果
        """
        if template_name not in self.prompt_templates:
            return ModelResponse(
                content="",
                model=model or self.model,
                prompt="",
                response_time=0,
                success=False,
                error_message=f"模板不存在: {template_name}"
            )

        template = self.prompt_templates[template_name]

        try:
            # 填充模板变量
            prompt = template.template.format(**variables)

            logger.info(f"使用模板生成: {template_name}")
            logger.debug(f"模板变量: {variables}")

            response = self.generate(prompt, model, options)

            # 添加模板信息到元数据
            if response.metadata is None:
                response.metadata = {}

            response.metadata.update({
                'template_name': template_name,
                'template_variables': variables,
                'template_category': template.category
            })

            return response

        except KeyError as e:
            return ModelResponse(
                content="",
                model=model or self.model,
                prompt="",
                response_time=0,
                success=False,
                error_message=f"模板变量缺失: {e}"
            )
        except Exception as e:
            return ModelResponse(
                content="",
                model=model or self.model,
                prompt="",
                response_time=0,
                success=False,
                error_message=f"模板处理失败: {e}"
            )

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            models = ollama.list()
            model_list = getattr(models, 'models', [])
            available_models = []
            for m in model_list:
                if hasattr(m, 'model'):
                    available_models.append(m.model)
                elif isinstance(m, dict) and 'name' in m:
                    available_models.append(m['name'])
                elif isinstance(m, str):
                    available_models.append(m)
            return available_models
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []

    def get_prompt_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """获取提示词模板列表"""
        templates = list(self.prompt_templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return templates

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取指定的提示词模板"""
        return self.prompt_templates.get(name)

    def add_template(self, template: PromptTemplate):
        """添加提示词模板"""
        self.prompt_templates[template.name] = template
        logger.info(f"添加模板: {template.name}")

    def reload_templates(self):
        """重新加载提示词模板"""
        self.prompt_templates.clear()
        self._load_prompt_templates()

    def get_client_info(self) -> Dict[str, Any]:
        """获取客户端信息"""
        return {
            'model': self.model,
            'base_url': self.base_url,
            'timeout': self.timeout,
            'prompts_dir': str(self.prompts_dir),
            'templates_count': len(self.prompt_templates),
            'default_options': self.default_options,
            'available_models': self.get_available_models()
        }
