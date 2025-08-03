#!/usr/bin/env python3
"""
API服务启动脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    try:
        print("🚀 启动离线文档知识图谱系统API服务...")
        print("📍 服务地址: http://localhost:8000")
        print("📖 API文档: http://localhost:8000/docs")

        import uvicorn
        uvicorn.run(
            "backend.app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
