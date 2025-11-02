#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页打包工具 - 启动脚本
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    try:
        # 检查依赖
        from main import WebPackager
        
        # 启动应用
        app = WebPackager()
        app.run()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖包:")
        print("pip install -r requirements.txt")
        input("按任意键退出...")
    except Exception as e:
        print(f"程序错误: {e}")
        input("按任意键退出...")

if __name__ == "__main__":
    main()