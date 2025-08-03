"""
Ollama客户端模块测试
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.services.ollama_client import (
    OllamaClient,
    ModelResponse,
    PromptTemplate,
    OllamaClientError
)


@pytest.fixture
def temp_prompts_dir():
    """创建临时提示词目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建测试提示词文件
        entity_template = temp_path / "entity_extraction.txt"
        with open(entity_template, 'w', encoding='utf-8') as f:
            f.write("请从以下文本中抽取{entity_type}实体：\n\n{text}\n\n请返回JSON格式。")

        query_template = temp_path / "graph_query.txt"
        with open(query_template, 'w', encoding='utf-8') as f:
            f.write("根据以下Schema生成Cypher查询：\n\nSchema: {schema}\n问题: {question}")

        yield temp_path


def test_ollama_client_init(temp_prompts_dir):
    """测试Ollama客户端初始化"""
    client = OllamaClient(
        model="test-model",
        base_url="http://test:11434",
        timeout=60,
        prompts_dir=str(temp_prompts_dir)
    )

    assert client.model == "test-model"
    assert client.base_url == "http://test:11434"
    assert client.timeout == 60
    assert client.prompts_dir == temp_prompts_dir
    assert len(client.prompt_templates) == 2


def test_prompt_template_loading(temp_prompts_dir):
    """测试提示词模板加载"""
    client = OllamaClient(prompts_dir=str(temp_prompts_dir))

    # 检查模板是否正确加载
    assert "entity_extraction" in client.prompt_templates
    assert "graph_query" in client.prompt_templates

    entity_template = client.prompt_templates["entity_extraction"]
    assert entity_template.name == "entity_extraction"
    assert "entity_type" in entity_template.variables
    assert "text" in entity_template.variables
    assert entity_template.category == "extraction"


def test_prompt_template_parsing():
    """测试提示词模板解析"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        template_file = temp_path / "test_template.txt"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write("Hello {name}, your age is {age}. Welcome to {place}!")

        client = OllamaClient(prompts_dir=str(temp_path))

        template = client.prompt_templates["test_template"]
        assert set(template.variables) == {"name", "age", "place"}


@patch('ollama.list')
def test_get_available_models(mock_list):
    """测试获取可用模型列表"""
    mock_list.return_value = {
        'models': [
            {'name': 'model1'},
            {'name': 'model2'},
            {'name': 'model3'}
        ]
    }

    client = OllamaClient()
    models = client.get_available_models()

    assert models == ['model1', 'model2', 'model3']


@patch('ollama.list')
@patch('ollama.generate')
def test_test_connection_success(mock_generate, mock_list):
    """测试连接测试成功"""
    mock_list.return_value = {
        'models': [{'name': 'qwen3:4b'}]
    }
    mock_generate.return_value = {'response': 'Hello!'}

    client = OllamaClient(model='qwen3:4b')
    result = client.test_connection()

    assert result is True


@patch('ollama.list')
def test_test_connection_model_not_available(mock_list):
    """测试连接测试失败（模型不可用）"""
    mock_list.return_value = {
        'models': [{'name': 'other-model'}]
    }

    client = OllamaClient(model='qwen3:4b')
    result = client.test_connection()

    assert result is False


@patch('ollama.generate')
def test_generate_success(mock_generate):
    """测试文本生成成功"""
    mock_generate.return_value = {
        'response': 'Generated text response'
    }

    client = OllamaClient()
    response = client.generate("Test prompt")

    assert response.success is True
    assert response.content == 'Generated text response'
    assert response.model == 'qwen3:4b'
    assert response.prompt == "Test prompt"
    assert response.response_time > 0


@patch('ollama.generate')
def test_generate_failure(mock_generate):
    """测试文本生成失败"""
    mock_generate.side_effect = Exception("Connection error")

    client = OllamaClient()
    response = client.generate("Test prompt")

    assert response.success is False
    assert response.error_message == "Connection error"
    assert response.content == ""


def test_generate_with_template_success(temp_prompts_dir):
    """测试使用模板生成成功"""
    with patch('ollama.generate') as mock_generate:
        mock_generate.return_value = {'response': 'Extracted entities: {...}'}

        client = OllamaClient(prompts_dir=str(temp_prompts_dir))

        response = client.generate_with_template(
            template_name="entity_extraction",
            variables={
                "entity_type": "Person",
                "text": "张三是工程师"
            }
        )

        assert response.success is True
        assert response.content == 'Extracted entities: {...}'
        assert response.metadata['template_name'] == "entity_extraction"


def test_generate_with_template_missing_template():
    """测试使用不存在的模板"""
    client = OllamaClient()

    response = client.generate_with_template(
        template_name="nonexistent_template",
        variables={}
    )

    assert response.success is False
    assert "模板不存在" in response.error_message


def test_generate_with_template_missing_variables(temp_prompts_dir):
    """测试模板变量缺失"""
    client = OllamaClient(prompts_dir=str(temp_prompts_dir))

    response = client.generate_with_template(
        template_name="entity_extraction",
        variables={"entity_type": "Person"}  # 缺少 text 变量
    )

    assert response.success is False
    assert "模板变量缺失" in response.error_message


def test_get_prompt_templates(temp_prompts_dir):
    """测试获取提示词模板"""
    client = OllamaClient(prompts_dir=str(temp_prompts_dir))

    # 获取所有模板
    all_templates = client.get_prompt_templates()
    assert len(all_templates) == 2

    # 按类别获取模板
    extraction_templates = client.get_prompt_templates(category="extraction")
    assert len(extraction_templates) == 1
    assert extraction_templates[0].name == "entity_extraction"

    query_templates = client.get_prompt_templates(category="query")
    assert len(query_templates) == 1
    assert query_templates[0].name == "graph_query"


def test_get_template(temp_prompts_dir):
    """测试获取指定模板"""
    client = OllamaClient(prompts_dir=str(temp_prompts_dir))

    template = client.get_template("entity_extraction")
    assert template is not None
    assert template.name == "entity_extraction"

    nonexistent = client.get_template("nonexistent")
    assert nonexistent is None


def test_add_template():
    """测试添加模板"""
    client = OllamaClient()

    new_template = PromptTemplate(
        name="custom_template",
        template="Custom template with {variable}",
        description="Custom template for testing",
        variables=["variable"],
        category="custom"
    )

    client.add_template(new_template)

    assert "custom_template" in client.prompt_templates
    retrieved = client.get_template("custom_template")
    assert retrieved.name == "custom_template"
    assert retrieved.category == "custom"


def test_model_response_dataclass():
    """测试ModelResponse数据类"""
    response = ModelResponse(
        content="Test content",
        model="test-model",
        prompt="Test prompt",
        response_time=1.5,
        success=True,
        metadata={"key": "value"}
    )

    assert response.content == "Test content"
    assert response.model == "test-model"
    assert response.prompt == "Test prompt"
    assert response.response_time == 1.5
    assert response.success is True
    assert response.error_message == ""
    assert response.metadata == {"key": "value"}


def test_prompt_template_dataclass():
    """测试PromptTemplate数据类"""
    template = PromptTemplate(
        name="test_template",
        template="Hello {name}",
        description="Test template",
        variables=["name"],
        category="test"
    )

    assert template.name == "test_template"
    assert template.template == "Hello {name}"
    assert template.description == "Test template"
    assert template.variables == ["name"]
    assert template.category == "test"


def test_get_client_info():
    """测试获取客户端信息"""
    with patch('ollama.list') as mock_list:
        mock_list.return_value = {'models': [{'name': 'test-model'}]}

        client = OllamaClient(model="test-model")
        info = client.get_client_info()

        assert info['model'] == "test-model"
        assert info['base_url'] == "http://localhost:11434"
        assert 'templates_count' in info
        assert 'default_options' in info
        assert 'available_models' in info


def test_reload_templates(temp_prompts_dir):
    """测试重新加载模板"""
    client = OllamaClient(prompts_dir=str(temp_prompts_dir))

    initial_count = len(client.prompt_templates)

    # 添加新的模板文件
    new_template = temp_prompts_dir / "new_template.txt"
    with open(new_template, 'w', encoding='utf-8') as f:
        f.write("New template with {param}")

    # 重新加载
    client.reload_templates()

    assert len(client.prompt_templates) == initial_count + 1
    assert "new_template" in client.prompt_templates
