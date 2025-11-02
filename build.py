#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页打包工具 - 自打包脚本
将工具本身打包成独立的exe文件
"""

import os
import sys
import subprocess
import tempfile
import shutil

def build_exe():
    """将工具打包成exe"""
    print("正在打包网页打包工具...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 复制必要文件到临时目录
        files_to_copy = [
            'main.py',
            'run.py', 
            'config.json',
            'requirements.txt'
        ]
        
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy2(file, os.path.join(temp_dir, file))
        
        # 创建spec文件
        spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'webview', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='网页打包工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
"""
        
        spec_file = os.path.join(temp_dir, "webpackager.spec")
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        # 使用PyInstaller打包
        print("正在使用PyInstaller打包...")
        
        cmd = [
            'pyinstaller',
            '--noconfirm',
            '--onefile',
            '--windowed',
            '--name', '网页打包工具',
            '--distpath', 'dist',
            '--workpath', os.path.join(temp_dir, 'build'),
            '--specpath', temp_dir,
            os.path.join(temp_dir, 'run.py')
        ]
        
        # 如果有图标文件，添加图标
        if os.path.exists('icon.ico'):
            cmd.extend(['--icon', 'icon.ico'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("打包成功完成！")
            print("生成的可执行文件位于: dist/网页打包工具.exe")
        else:
            print(f"打包失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        return False
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return True

def main():
    """主函数"""
    print("网页打包工具 - 自打包脚本")
    print("=" * 50)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
    except ImportError:
        print("错误: 未找到PyInstaller，请先安装:")
        print("pip install pyinstaller")
        input("按任意键退出...")
        return
    
    # 执行打包
    if build_exe():
        print("\n打包完成！")
    else:
        print("\n打包失败！")
    
    input("按任意键退出...")

if __name__ == "__main__":
    main()