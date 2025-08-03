"""
文档扫描模块测试
"""

import pytest
import tempfile
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.services.document_scanner import DocumentScanner, DocumentInfo


@pytest.fixture
def temp_docs_dir():
    """创建临时文档目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建测试文件
        (temp_path / "test1.docx").touch()
        (temp_path / "test2.xlsx").touch()
        (temp_path / "test3.pdf").touch()
        (temp_path / "test4.txt").touch()
        (temp_path / "ignore.jpg").touch()  # 不支持的格式

        # 创建子目录
        sub_dir = temp_path / "subdir"
        sub_dir.mkdir()
        (sub_dir / "sub_test.docx").touch()

        yield temp_path


def test_document_scanner_init():
    """测试文档扫描器初始化"""
    scanner = DocumentScanner(
        scan_directories=["./test_dir"],
        supported_formats=[".docx", ".xlsx"]
    )

    assert len(scanner.scan_directories) == 1
    assert scanner.supported_formats == [".docx", ".xlsx"]
    assert not scanner.is_monitoring


def test_scan_directories(temp_docs_dir):
    """测试目录扫描功能"""
    scanner = DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx", ".xlsx", ".pdf", ".txt"]
    )

    documents = scanner.scan_all_directories()

    # 应该找到5个支持的文件（包括子目录中的1个）
    assert len(documents) == 5

    # 检查文件类型
    file_types = [doc.file_type for doc in documents]
    assert ".docx" in file_types
    assert ".xlsx" in file_types
    assert ".pdf" in file_types
    assert ".txt" in file_types

    # 检查统计信息
    stats = scanner.get_stats()
    assert stats['total_files'] == 6  # 包括不支持的.jpg文件
    assert stats['supported_files'] == 5


def test_supported_file_filter(temp_docs_dir):
    """测试文件格式过滤"""
    scanner = DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx", ".xlsx"]  # 只支持这两种格式
    )

    documents = scanner.scan_all_directories()

    # 应该只找到2个docx和xlsx文件（包括子目录中的1个docx）
    assert len(documents) == 3

    file_types = [doc.file_type for doc in documents]
    assert all(ft in [".docx", ".xlsx"] for ft in file_types)


def test_document_info_structure(temp_docs_dir):
    """测试文档信息结构"""
    scanner = DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx"]
    )

    documents = scanner.scan_all_directories()

    assert len(documents) > 0
    doc = documents[0]

    # 检查DocumentInfo结构
    assert hasattr(doc, 'file_path')
    assert hasattr(doc, 'file_name')
    assert hasattr(doc, 'file_size')
    assert hasattr(doc, 'file_type')
    assert hasattr(doc, 'created_time')
    assert hasattr(doc, 'modified_time')
    assert hasattr(doc, 'status')

    assert doc.status == "discovered"
    assert doc.file_type == ".docx"


def test_document_status_update(temp_docs_dir):
    """测试文档状态更新"""
    scanner = DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx"]
    )

    documents = scanner.scan_all_directories()
    assert len(documents) > 0

    doc = documents[0]
    file_path = doc.file_path

    # 更新状态
    scanner.update_document_status(file_path, "processing")

    updated_doc = scanner.get_document(file_path)
    assert updated_doc.status == "processing"


def test_get_documents_by_status(temp_docs_dir):
    """测试按状态获取文档"""
    scanner = DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx", ".xlsx"]
    )

    documents = scanner.scan_all_directories()

    # 更新部分文档状态
    if len(documents) >= 2:
        scanner.update_document_status(documents[0].file_path, "processing")
        scanner.update_document_status(documents[1].file_path, "processed")

    # 测试按状态过滤
    discovered_docs = scanner.get_documents("discovered")
    processing_docs = scanner.get_documents("processing")
    processed_docs = scanner.get_documents("processed")

    assert len(processing_docs) == 1
    assert len(processed_docs) == 1
    assert len(discovered_docs) == len(documents) - 2


def test_stats_collection(temp_docs_dir):
    """测试统计信息收集"""
    scanner = DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx", ".xlsx", ".pdf", ".txt"]
    )

    scanner.scan_all_directories()
    stats = scanner.get_stats()

    # 检查统计信息结构
    assert 'total_files' in stats
    assert 'supported_files' in stats
    assert 'current_documents' in stats
    assert 'status_breakdown' in stats
    assert 'last_scan_time' in stats

    # 检查状态分布
    assert 'discovered' in stats['status_breakdown']
    assert stats['status_breakdown']['discovered'] == stats['supported_files']


def test_nonexistent_directory():
    """测试不存在的目录"""
    scanner = DocumentScanner(
        scan_directories=["/nonexistent/directory"],
        supported_formats=[".docx"]
    )

    documents = scanner.scan_all_directories()
    assert len(documents) == 0

    stats = scanner.get_stats()
    assert stats['total_files'] == 0
    assert stats['supported_files'] == 0


def test_file_monitoring_start_stop(temp_docs_dir):
    """测试文件监控启动和停止"""
    scanner = DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx"]
    )

    # 测试启动监控
    assert not scanner.is_monitoring
    scanner.start_monitoring()
    assert scanner.is_monitoring

    # 测试停止监控
    scanner.stop_monitoring()
    assert not scanner.is_monitoring


def test_context_manager(temp_docs_dir):
    """测试上下文管理器"""
    with DocumentScanner(
        scan_directories=[str(temp_docs_dir)],
        supported_formats=[".docx"]
    ) as scanner:
        documents = scanner.scan_all_directories()
        assert len(documents) > 0

    # 上下文退出后监控应该停止
    assert not scanner.is_monitoring
