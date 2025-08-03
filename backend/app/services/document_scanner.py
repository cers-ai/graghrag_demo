"""
文档扫描服务模块
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger


@dataclass
class DocumentInfo:
    """文档信息数据类"""
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    created_time: datetime
    modified_time: datetime
    status: str = "discovered"  # discovered, processing, processed, error


class DocumentEventHandler(FileSystemEventHandler):
    """文档文件系统事件处理器"""

    def __init__(self, scanner: 'DocumentScanner'):
        self.scanner = scanner

    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            self.scanner._handle_file_event(event.src_path, "created")

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            self.scanner._handle_file_event(event.src_path, "modified")

    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            self.scanner._handle_file_event(event.src_path, "deleted")


class DocumentScanner:
    """文档扫描器"""

    def __init__(self,
                 scan_directories: List[str],
                 supported_formats: List[str] = None,
                 callback: Optional[Callable] = None):
        """
        初始化文档扫描器

        Args:
            scan_directories: 扫描目录列表
            supported_formats: 支持的文件格式列表
            callback: 文件事件回调函数
        """
        self.scan_directories = [Path(d) for d in scan_directories]
        self.supported_formats = supported_formats or ['.docx', '.xlsx', '.pdf', '.txt']
        self.callback = callback

        # 文档存储
        self.documents: Dict[str, DocumentInfo] = {}

        # 监控相关
        self.observer = Observer()
        self.is_monitoring = False

        # 统计信息
        self.stats = {
            'total_files': 0,
            'supported_files': 0,
            'new_files': 0,
            'modified_files': 0,
            'deleted_files': 0,
            'last_scan_time': None
        }

        logger.info(f"文档扫描器初始化完成")
        logger.info(f"扫描目录: {[str(d) for d in self.scan_directories]}")
        logger.info(f"支持格式: {self.supported_formats}")

    def _is_supported_file(self, file_path: Path) -> bool:
        """检查文件是否为支持的格式"""
        return file_path.suffix.lower() in self.supported_formats

    def _get_file_info(self, file_path: Path) -> Optional[DocumentInfo]:
        """获取文件信息"""
        try:
            if not file_path.exists():
                return None

            stat = file_path.stat()

            return DocumentInfo(
                file_path=str(file_path.absolute()),
                file_name=file_path.name,
                file_size=stat.st_size,
                file_type=file_path.suffix.lower(),
                created_time=datetime.fromtimestamp(stat.st_ctime),
                modified_time=datetime.fromtimestamp(stat.st_mtime)
            )
        except Exception as e:
            logger.error(f"获取文件信息失败 {file_path}: {e}")
            return None

    def _handle_file_event(self, file_path: str, event_type: str):
        """处理文件事件"""
        path = Path(file_path)

        if not self._is_supported_file(path):
            return

        logger.info(f"文件事件: {event_type} - {file_path}")

        if event_type == "deleted":
            if file_path in self.documents:
                del self.documents[file_path]
                self.stats['deleted_files'] += 1
        else:
            file_info = self._get_file_info(path)
            if file_info:
                is_new = file_path not in self.documents
                self.documents[file_path] = file_info

                if is_new:
                    self.stats['new_files'] += 1
                elif event_type == "modified":
                    self.stats['modified_files'] += 1

        # 调用回调函数
        if self.callback:
            try:
                self.callback(file_path, event_type)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")

    def scan_all_directories(self) -> List[DocumentInfo]:
        """扫描所有目录"""
        logger.info("开始扫描目录...")

        all_documents = []
        self.stats['total_files'] = 0
        self.stats['supported_files'] = 0

        for scan_dir in self.scan_directories:
            if not scan_dir.exists():
                logger.warning(f"扫描目录不存在: {scan_dir}")
                continue

            logger.info(f"扫描目录: {scan_dir}")
            documents = self._scan_directory(scan_dir)
            all_documents.extend(documents)

        # 更新文档存储
        for doc in all_documents:
            self.documents[doc.file_path] = doc

        self.stats['last_scan_time'] = datetime.now()

        logger.info(f"扫描完成: 总文件 {self.stats['total_files']}, "
                   f"支持文件 {self.stats['supported_files']}")

        return all_documents

    def _scan_directory(self, directory: Path) -> List[DocumentInfo]:
        """扫描单个目录"""
        documents = []

        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    self.stats['total_files'] += 1

                    if self._is_supported_file(file_path):
                        self.stats['supported_files'] += 1

                        file_info = self._get_file_info(file_path)
                        if file_info:
                            documents.append(file_info)
                            logger.debug(f"发现文档: {file_path}")

        except Exception as e:
            logger.error(f"扫描目录失败 {directory}: {e}")

        return documents

    def start_monitoring(self):
        """开始监控文件变化"""
        if self.is_monitoring:
            logger.warning("文件监控已在运行")
            return

        logger.info("开始文件监控...")

        event_handler = DocumentEventHandler(self)

        for scan_dir in self.scan_directories:
            if scan_dir.exists():
                self.observer.schedule(event_handler, str(scan_dir), recursive=True)
                logger.info(f"监控目录: {scan_dir}")

        self.observer.start()
        self.is_monitoring = True
        logger.info("文件监控已启动")

    def stop_monitoring(self):
        """停止监控文件变化"""
        if not self.is_monitoring:
            return

        logger.info("停止文件监控...")
        self.observer.stop()
        self.observer.join()
        self.is_monitoring = False
        logger.info("文件监控已停止")

    def get_documents(self, status: Optional[str] = None) -> List[DocumentInfo]:
        """获取文档列表"""
        if status:
            return [doc for doc in self.documents.values() if doc.status == status]
        return list(self.documents.values())

    def get_document(self, file_path: str) -> Optional[DocumentInfo]:
        """获取单个文档信息"""
        return self.documents.get(file_path)

    def update_document_status(self, file_path: str, status: str):
        """更新文档状态"""
        if file_path in self.documents:
            self.documents[file_path].status = status
            logger.debug(f"更新文档状态: {file_path} -> {status}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        current_stats = self.stats.copy()
        current_stats['current_documents'] = len(self.documents)
        current_stats['status_breakdown'] = {}

        for doc in self.documents.values():
            status = doc.status
            current_stats['status_breakdown'][status] = \
                current_stats['status_breakdown'].get(status, 0) + 1

        return current_stats

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_monitoring()
