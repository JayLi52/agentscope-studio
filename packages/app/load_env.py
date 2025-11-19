# -*- coding: utf-8 -*-
"""Load environment variables from .env file."""
import os
from pathlib import Path
from typing import Optional


def load_env(env_file: str = ".env", search_parent_dirs: bool = True, start_dir: Optional[Path] = None) -> bool:
    """
    从指定的 .env 文件加载环境变量到 os.environ 中
    
    Args:
        env_file: .env 文件名，默认为 ".env"
        search_parent_dirs: 是否在父目录中搜索 .env 文件，默认为 True
        start_dir: 开始搜索的目录，默认为调用者脚本所在目录
    
    Returns:
        bool: 如果成功加载返回 True，否则返回 False
    
    Examples:
        >>> load_env()  # 从脚本所在目录或父目录加载 .env
        >>> load_env(".env.local")  # 加载指定的 .env 文件
        >>> load_env(search_parent_dirs=False)  # 仅从脚本所在目录加载
    """
    # 如果没有指定起始目录，使用调用者脚本所在的目录
    if start_dir is None:
        import inspect
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        start_dir = Path(caller_file).parent
    
    current_dir = start_dir
    env_path: Optional[Path] = None
    
    # 搜索 .env 文件
    if search_parent_dirs:
        # 从当前目录向上查找，直到找到 .env 文件或到达根目录
        search_dir = current_dir
        while True:
            candidate = search_dir / env_file
            if candidate.exists() and candidate.is_file():
                env_path = candidate
                break
            
            # 到达根目录
            if search_dir.parent == search_dir:
                break
            search_dir = search_dir.parent
    else:
        # 仅在当前目录查找
        candidate = current_dir / env_file
        if candidate.exists() and candidate.is_file():
            env_path = candidate
    
    if env_path is None:
        return False
    
    # 读取并解析 .env 文件
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析 KEY=VALUE 格式
                if '=' not in line:
                    continue
                
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                
                # 移除引号（单引号或双引号）
                if len(value) >= 2:
                    if (value[0] == '"' and value[-1] == '"') or \
                       (value[0] == "'" and value[-1] == "'"):
                        value = value[1:-1]
                
                # 只有当环境变量不存在时才设置
                if key and key not in os.environ:
                    os.environ[key] = value
        
        return True
    
    except Exception as e:
        print(f"加载 .env 文件失败: {e}")
        return False
