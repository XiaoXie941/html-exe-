#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页打包工具 - 基于Chromium核心的独立桌面应用程序打包工具
"""

import os
import sys
import json
import tempfile
import shutil
import threading
import time
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import webview
import requests
from PIL import Image, ImageTk

class WebPackager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("网页打包工具 v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置图标
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 加载配置文件
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.user_config = self.load_user_config()
        
        self.setup_ui()
        
        # 打包参数
        self.pack_params = {
            'mode': 'url',
            'source': '',
            'window_title': '我的网页应用',
            'window_width': 1024,
            'window_height': 768,
            'output_dir': '',
            'icon_path': ''
        }
        
        # 状态变量
        self.is_packaging = False
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建滚动框架
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 创建主框架
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置滚动框架
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="网页打包工具", font=("微软雅黑", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 打包模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="打包模式", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        mode_frame.columnconfigure(1, weight=1)
        
        self.mode_var = tk.StringVar(value="url")
        
        ttk.Radiobutton(mode_frame, text="网页URL", variable=self.mode_var, 
                       value="url", command=self.on_mode_change).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="本地HTML文件", variable=self.mode_var, 
                       value="file", command=self.on_mode_change).grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="本地文件夹", variable=self.mode_var, 
                       value="folder", command=self.on_mode_change).grid(row=2, column=0, sticky=tk.W)
        
        # 源文件/URL输入
        source_frame = ttk.LabelFrame(main_frame, text="源文件/URL", padding="10")
        source_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        source_frame.columnconfigure(1, weight=1)
        
        self.source_var = tk.StringVar()
        self.source_entry = ttk.Entry(source_frame, textvariable=self.source_var)
        self.source_entry.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.browse_btn = ttk.Button(source_frame, text="浏览...", command=self.browse_source)
        self.browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        self.preview_btn = ttk.Button(source_frame, text="预览", command=self.preview_source)
        self.preview_btn.grid(row=1, column=0, pady=(5, 0))
        
        # 文件夹结构显示（仅文件夹模式）
        self.tree_frame = ttk.LabelFrame(main_frame, text="文件夹结构", padding="10")
        self.tree_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.tree_frame.columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.tree_frame, height=8, show="tree")
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree_frame.grid_remove()  # 初始隐藏
        
        # 参数设置
        params_frame = ttk.LabelFrame(main_frame, text="窗口参数", padding="10")
        params_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 窗口标题
        ttk.Label(params_frame, text="窗口标题:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.title_var = tk.StringVar(value="我的网页应用")
        ttk.Entry(params_frame, textvariable=self.title_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        
        # 窗口尺寸
        ttk.Label(params_frame, text="窗口宽度:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.width_var = tk.StringVar(value="1024")
        ttk.Entry(params_frame, textvariable=self.width_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(params_frame, text="窗口高度:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.height_var = tk.StringVar(value="768")
        ttk.Entry(params_frame, textvariable=self.height_var, width=10).grid(row=1, column=3, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 图标设置
        ttk.Label(params_frame, text="应用图标:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.icon_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.icon_var).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        ttk.Button(params_frame, text="选择...", command=self.browse_icon).grid(row=2, column=2, padx=(5, 0), pady=2)
        
        # 输出目录
        ttk.Label(params_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, pady=2)
        # 设置默认输出路径为当前目录下的Pack文件夹
        default_output_dir = os.path.join(os.path.dirname(__file__), "Pack")
        self.output_var = tk.StringVar(value=default_output_dir)
        ttk.Entry(params_frame, textvariable=self.output_var).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        ttk.Button(params_frame, text="选择...", command=self.browse_output).grid(row=3, column=2, padx=(5, 0), pady=2)
        
        params_frame.columnconfigure(1, weight=1)
        
        # 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="打包进度", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.progress['value'] = 0  # 初始化为0，避免显示异常
        
        self.status_var = tk.StringVar(value="准备就绪")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 日志显示
        log_frame = ttk.LabelFrame(main_frame, text="日志信息", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))
        
        self.pack_btn = ttk.Button(button_frame, text="开始打包", command=self.start_packaging)
        self.pack_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="清除日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT)
        
        # 配置主框架权重
        main_frame.rowconfigure(6, weight=1)
        
        self.log("网页打包工具已启动，请选择打包模式并配置参数。")
        
        # 加载上次的用户配置
        self.load_last_config()
        
    def load_last_config(self):
        """加载上次的用户配置"""
        # 设置上次使用的模式
        last_mode = self.user_config.get("last_mode", "url")
        self.mode_var.set(last_mode)
        self.on_mode_change()
        
        # 设置上次使用的源文件/URL
        # 从最近使用记录中获取最后一个使用的源文件
        recent_sources = self.user_config.get("recent_sources", [])
        if recent_sources:
            last_source = recent_sources[0]["source"]
            last_source_mode = recent_sources[0]["mode"]
            
            # 直接设置源文件，不检查模式匹配
            self.source_var.set(last_source)
            
            # 如果是文件夹模式，加载文件夹结构
            if last_source_mode == "folder" and os.path.exists(last_source):
                self.load_folder_structure(last_source)
                
            self.log(f"加载最近使用记录: 模式={last_source_mode}, 源文件={last_source}")
        else:
            self.log("没有找到最近使用记录")
        
        # 设置上次使用的输出目录
        last_output_dir = self.user_config.get("last_output_dir", os.path.join(os.path.dirname(__file__), "Pack"))
        self.output_var.set(last_output_dir)
        
        # 设置窗口尺寸
        window_settings = self.user_config.get("window_settings", {})
        if window_settings:
            width = window_settings.get("width", 800)
            height = window_settings.get("height", 600)
            self.root.geometry(f"{width}x{height}")
        
        self.log(f"已加载上次的用户配置: 模式={last_mode}, 输出目录={last_output_dir}")
        
    def on_mode_change(self):
        """打包模式改变时的处理"""
        mode = self.mode_var.get()
        
        if mode == "folder":
            self.tree_frame.grid()
            self.browse_btn.config(text="选择文件夹...")
        else:
            self.tree_frame.grid_remove()
            self.browse_btn.config(text="浏览...")
        
        if mode == "url":
            self.source_entry.config(state="normal")
            self.preview_btn.config(state="normal")
        elif mode == "file":
            self.source_entry.config(state="normal")
            self.preview_btn.config(state="normal")
        else:  # folder模式
            self.source_entry.config(state="normal")
            self.preview_btn.config(state="normal")
    
    def browse_source(self):
        """浏览源文件/文件夹"""
        mode = self.mode_var.get()
        
        if mode == "url":
            url = self.source_var.get()
            if url:
                self.source_var.set(url)
        elif mode == "file":
            file_path = filedialog.askopenfilename(
                title="选择HTML文件",
                filetypes=[("HTML文件", "*.html;*.htm"), ("所有文件", "*.*")]
            )
            if file_path:
                self.source_var.set(file_path)
        else:  # folder模式
            folder_path = filedialog.askdirectory(title="选择文件夹")
            if folder_path:
                self.source_var.set(folder_path)
                self.load_folder_structure(folder_path)
    
    def browse_icon(self):
        """选择应用图标"""
        file_path = filedialog.askopenfilename(
            title="选择图标文件",
            filetypes=[("图标文件", "*.ico;*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")]
        )
        if file_path:
            self.icon_var.set(file_path)
    
    def browse_output(self):
        """选择输出目录"""
        folder_path = filedialog.askdirectory(title="选择输出目录")
        if folder_path:
            self.output_var.set(folder_path)
    
    def load_folder_structure(self, folder_path):
        """加载文件夹结构"""
        # 清空现有树结构
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        def add_tree_items(parent, path):
            try:
                for item in sorted(os.listdir(path)):
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        node = self.tree.insert(parent, "end", text=item, values=["文件夹"])
                        add_tree_items(node, full_path)
                    else:
                        self.tree.insert(parent, "end", text=item, values=["文件"])
            except PermissionError:
                pass
        
        root_node = self.tree.insert("", "end", text=folder_path, values=["根目录"])
        add_tree_items(root_node, folder_path)
        self.tree.item(root_node, open=True)
    
    def preview_source(self):
        """预览源文件/网页"""
        mode = self.mode_var.get()
        source = self.source_var.get()
        
        if not source:
            messagebox.showwarning("警告", "请先选择或输入源文件/URL")
            return
        
        try:
            if mode == "url":
                if not source.startswith(('http://', 'https://')):
                    source = 'http://' + source
                webbrowser.open(source)
                self.log(f"已在浏览器中打开: {source}")
            elif mode == "file":
                if os.path.exists(source):
                    webbrowser.open('file://' + os.path.abspath(source))
                    self.log(f"已预览文件: {source}")
                else:
                    messagebox.showerror("错误", "文件不存在")
            else:  # folder模式
                if os.path.exists(source):
                    # 查找HTML文件
                    html_files = list(Path(source).glob("*.html")) + list(Path(source).glob("*.htm"))
                    if html_files:
                        webbrowser.open('file://' + str(html_files[0].absolute()))
                        self.log(f"已预览文件夹中的HTML文件: {html_files[0]}")
                    else:
                        messagebox.showinfo("信息", "文件夹中没有找到HTML文件")
                else:
                    messagebox.showerror("错误", "文件夹不存在")
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {str(e)}")
    
    def validate_inputs(self):
        """验证输入参数"""
        mode = self.mode_var.get()
        source = self.source_var.get()
        
        if not source:
            messagebox.showwarning("警告", "请选择或输入源文件/URL")
            return False
        
        if mode == "file" and not os.path.exists(source):
            messagebox.showerror("错误", "选择的文件不存在")
            return False
        
        if mode == "folder" and not os.path.exists(source):
            messagebox.showerror("错误", "选择的文件夹不存在")
            return False
        
        output_dir = self.output_var.get()
        if not output_dir:
            messagebox.showwarning("警告", "请选择输出目录")
            return False
        
        # 自动创建输出目录（如果不存在）
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建输出目录: {str(e)}")
            return False
        
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            if width < 400 or height < 300:
                messagebox.showwarning("警告", "窗口尺寸不能小于400x300")
                return False
        except ValueError:
            messagebox.showerror("错误", "窗口尺寸必须为数字")
            return False
        
        return True
    
    def start_packaging(self):
        """开始打包"""
        if self.is_packaging:
            return
        
        if not self.validate_inputs():
            return
        
        self.is_packaging = True
        self.pack_btn.config(state="disabled")
        self.progress['value'] = 10  # 开始打包，设置初始进度
        
        # 在新线程中执行打包
        thread = threading.Thread(target=self.package_thread)
        thread.daemon = True
        thread.start()
    
    def package_thread(self):
        """打包线程"""
        try:
            self.log("开始打包过程...")
            
            # 收集参数
            params = {
                'mode': self.mode_var.get(),
                'source': self.source_var.get(),
                'window_title': self.title_var.get(),
                'window_width': int(self.width_var.get()),
                'window_height': int(self.height_var.get()),
                'output_dir': self.output_var.get(),
                'icon_path': self.icon_var.get()
            }
            
            # 创建应用文件
            self.create_application(params)
            
            # 打包完成
            self.root.after(0, self.packaging_complete)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.packaging_error(error_msg))
    
    def create_application(self, params):
        """创建应用程序"""
        self.log("正在创建应用配置...")
        
        # 创建临时工作目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 为每个软件创建独立的编号文件夹
            pack_dir = params['output_dir']
            os.makedirs(pack_dir, exist_ok=True)
            
            # 查找已存在的编号文件夹，确定下一个编号
            existing_folders = [d for d in os.listdir(pack_dir) if d.isdigit() and os.path.isdir(os.path.join(pack_dir, d))]
            next_number = 1
            if existing_folders:
                next_number = max(int(folder) for folder in existing_folders) + 1
            
            # 创建编号文件夹
            numbered_folder = os.path.join(pack_dir, str(next_number))
            os.makedirs(numbered_folder, exist_ok=True)
            
            self.log(f"创建软件文件夹: {numbered_folder}")
            
            # 创建主应用文件
            app_content = self.generate_app_code(params)
            app_file = os.path.join(temp_dir, "app.py")
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(app_content)
            
            self.log("应用代码生成完成")
            
            # 复制图标文件（如果有）
            if params['icon_path'] and os.path.exists(params['icon_path']):
                icon_ext = os.path.splitext(params['icon_path'])[1].lower()
                if icon_ext == '.ico':
                    shutil.copy2(params['icon_path'], os.path.join(temp_dir, "icon.ico"))
                else:
                    # 转换其他格式为ICO
                    self.convert_to_ico(params['icon_path'], os.path.join(temp_dir, "icon.ico"))
            
            # 复制HTML文件到临时目录（对于文件和文件夹模式）
            if params['mode'] == 'file':
                # 复制单个HTML文件
                html_file_name = os.path.basename(params['source'])
                shutil.copy2(params['source'], os.path.join(temp_dir, html_file_name))
                self.log(f"复制HTML文件: {html_file_name}")
            elif params['mode'] == 'folder':
                # 复制整个文件夹
                for root, dirs, files in os.walk(params['source']):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, params['source'])
                        dst_path = os.path.join(temp_dir, rel_path)
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                self.log(f"复制文件夹内容: {params['source']}")
            
            # 创建spec文件用于PyInstaller
            spec_content = self.generate_spec_file(params, temp_dir)
            spec_file = os.path.join(temp_dir, "app.spec")
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            self.log("配置文件生成完成")
            
            # 使用PyInstaller打包
            self.log("正在使用PyInstaller打包...")
            import subprocess
            
            output_name = params['window_title'].replace(' ', '_')
            
            # 构建PyInstaller命令
            cmd = [
                'pyinstaller',
                '--noconfirm',
                '--onefile',
                '--windowed',
                '--name', output_name,
                '--distpath', numbered_folder,  # 输出到编号文件夹
                '--workpath', os.path.join(temp_dir, 'build'),
                '--specpath', temp_dir,
            ]
            
            # 添加数据文件
            if params['mode'] == 'file':
                # 文件模式：添加单个HTML文件
                cmd.extend(['--add-data', f"{params['source']};."])
            elif params['mode'] == 'folder':
                # 文件夹模式：添加整个文件夹
                cmd.extend(['--add-data', f"{params['source']};."])
            
            cmd.append(app_file)
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=temp_dir)
            
            if result.returncode == 0:
                self.log("打包成功完成！")
                exe_path = os.path.join(numbered_folder, f"{output_name}.exe")
                self.log(f"生成的可执行文件: {exe_path}")
                
                # 复制HTML文件到编号文件夹（便于用户查看）
                if params['mode'] == 'file':
                    html_file_name = os.path.basename(params['source'])
                    shutil.copy2(params['source'], os.path.join(numbered_folder, html_file_name))
                elif params['mode'] == 'folder':
                    shutil.copytree(params['source'], os.path.join(numbered_folder, "web_content"), dirs_exist_ok=True)
                
                # 记录用户选择的HTML地址到配置文件
                self.add_recent_source(params['source'], params['mode'])
                
                self.log(f"软件已保存到: {numbered_folder}")
            else:
                raise Exception(f"PyInstaller打包失败: {result.stderr}")
                
        finally:
            # 清理临时文件
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def generate_app_code(self, params):
        """生成应用代码"""
        if params['mode'] == 'url':
            content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import webview

if __name__ == "__main__":
    webview.create_window(
        '{params['window_title']}',
        '{params['source']}',
        width={params['window_width']},
        height={params['window_height']},
        text_select=True,
        confirm_close=False
    )
    webview.start()
"""
        else:
            # 对于文件和文件夹模式，需要先复制文件到临时目录
            content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import webview

if __name__ == "__main__":
    # 获取资源路径
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件
        resource_path = sys._MEIPASS
    else:
        # 开发环境
        resource_path = os.path.dirname(os.path.abspath(__file__))
    
    # 根据模式确定要加载的文件
    """
            
            if params['mode'] == 'file':
                content += f"""
    # 文件模式 - 直接加载HTML文件
    html_file = os.path.join(resource_path, '{os.path.basename(params['source'])}')
    """
            else:  # folder模式
                content += f"""
    # 文件夹模式 - 查找HTML文件
    html_files = [f for f in os.listdir(resource_path) if f.lower().endswith(('.html', '.htm'))]
    if html_files:
        html_file = os.path.join(resource_path, html_files[0])
    else:
        print("未找到HTML文件")
        sys.exit(1)
    """
            
            content += f"""
    
    # 创建窗口 - 使用文件协议加载本地HTML文件
    webview.create_window(
        '{params['window_title']}',
        f"file://{{html_file}}",
        width={params['window_width']},
        height={params['window_height']},
        text_select=True,
        confirm_close=False
    )
    webview.start()
"""
        
        return content
    
    def generate_spec_file(self, params, temp_dir):
        """生成PyInstaller spec文件"""
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
"""
        
        # 添加数据文件
        if params['mode'] == 'file':
            spec_content += f"""
a.datas += [('{os.path.basename(params['source'])}', '{params['source']}', 'DATA')]
"""
        elif params['mode'] == 'folder':
            # 添加整个文件夹的内容
            for root, dirs, files in os.walk(params['source']):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, params['source'])
                    temp_file_path = os.path.join(temp_dir, rel_path)
                    spec_content += f"a.datas += [('{rel_path}', '{full_path}', 'DATA')]\n"
        
        # 添加图标
        if params['icon_path'] and os.path.exists(params['icon_path']):
            spec_content += f"""

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{params['window_title'].replace(' ', '_')}',
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
    icon='icon.ico',
)
"""
        else:
            spec_content += f"""

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{params['window_title'].replace(' ', '_')}',
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
)
"""
        
        return spec_content
    
    def convert_to_ico(self, input_path, output_path):
        """将图片转换为ICO格式"""
        try:
            with Image.open(input_path) as img:
                # 转换为RGBA模式（如果需要）
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 调整尺寸为ICO标准尺寸
                sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                
                # 创建不同尺寸的图标
                ico_images = []
                for size in sizes:
                    resized_img = img.resize(size, Image.Resampling.LANCZOS)
                    ico_images.append(resized_img)
                
                # 保存为ICO
                ico_images[0].save(output_path, format='ICO', sizes=[(img.width, img.height) for img in ico_images])
                
            self.log(f"图标转换完成: {input_path} -> {output_path}")
        except Exception as e:
            self.log(f"图标转换失败: {str(e)}")
    
    def packaging_complete(self):
        """打包完成"""
        self.is_packaging = False
        self.pack_btn.config(state="normal")
        self.progress['value'] = 100  # 设置为100%完成
        self.status_var.set("打包完成")
        
        messagebox.showinfo("完成", "打包成功完成！")
    
    def packaging_error(self, error_msg):
        """打包错误"""
        self.is_packaging = False
        self.pack_btn.config(state="normal")
        self.progress['value'] = 0  # 重置为0，表示打包失败
        self.status_var.set("打包失败")
        
        self.log(f"打包错误: {error_msg}")
        messagebox.showerror("错误", f"打包失败: {error_msg}")
    
    def log(self, message):
        """添加日志信息"""
        def update_log():
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.status_var.set(message)
        
        self.root.after(0, update_log)
    
    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)
        self.status_var.set("准备就绪")
    
    def load_user_config(self):
        """加载用户配置，如果没有配置文件则自动生成"""
        default_config = {
            "recent_sources": [],
            "last_mode": "url",
            "last_output_dir": os.path.join(os.path.dirname(__file__), "Pack"),
            "window_settings": {
                "width": 800,
                "height": 600
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置和用户配置
                    merged_config = self.merge_configs(default_config, config)
                    self.log("已加载现有配置文件")
                    return merged_config
            else:
                # 如果配置文件不存在，自动生成一个默认配置文件
                self.log("配置文件不存在，正在生成默认配置文件...")
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                self.log(f"已生成默认配置文件: {self.config_file}")
                return default_config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.log(f"加载配置文件失败: {e}")
            # 即使加载失败也返回默认配置
            return default_config
    
    def merge_configs(self, default_config, user_config):
        """合并默认配置和用户配置"""
        merged = default_config.copy()
        
        for key, value in user_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] = value
        
        return merged
    
    def save_user_config(self):
        """保存用户配置到config.json文件"""
        try:
            # 更新当前配置
            self.user_config["last_mode"] = self.mode_var.get()
            self.user_config["last_output_dir"] = self.output_var.get()
            
            # 保存窗口设置
            self.user_config["window_settings"] = {
                "width": self.root.winfo_width(),
                "height": self.root.winfo_height()
            }
            
            # 只写入必要的配置信息到config.json
            config_to_save = {
                "recent_sources": self.user_config.get("recent_sources", []),
                "last_mode": self.user_config.get("last_mode", "url"),
                "last_output_dir": self.user_config.get("last_output_dir", os.path.join(os.path.dirname(__file__), "Pack")),
                "window_settings": self.user_config.get("window_settings", {"width": 800, "height": 600})
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
                
            self.log("配置已保存到config.json")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            self.log(f"保存配置失败: {e}")
    
    def add_recent_source(self, source, mode):
        """添加最近使用的源文件/URL"""
        if not source:
            return
        
        # 创建记录
        record = {
            "source": source,
            "mode": mode,
            "timestamp": time.time()
        }
        
        # 检查是否已存在
        for i, recent in enumerate(self.user_config.get("recent_sources", [])):
            if recent["source"] == source and recent["mode"] == mode:
                # 更新时间戳并移到最前面
                self.user_config["recent_sources"].pop(i)
                break
        
        # 添加到最前面
        self.user_config.setdefault("recent_sources", []).insert(0, record)
        
        # 限制最多保存10个记录
        if len(self.user_config["recent_sources"]) > 10:
            self.user_config["recent_sources"] = self.user_config["recent_sources"][:10]
        
        # 保存配置
        self.save_user_config()
    
    def load_recent_sources(self):
        """加载最近使用的源文件/URL到界面"""
        recent_sources = self.user_config.get("recent_sources", [])
        
        if not recent_sources:
            return
        
        # 创建最近文件菜单
        if hasattr(self, 'recent_menu'):
            self.recent_menu.delete(0, tk.END)
        else:
            # 创建菜单栏
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)
            
            # 创建文件菜单
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="文件", menu=file_menu)
            
            # 创建最近文件子菜单
            self.recent_menu = tk.Menu(file_menu, tearoff=0)
            file_menu.add_cascade(label="最近使用", menu=self.recent_menu)
            file_menu.add_separator()
            file_menu.add_command(label="退出", command=self.root.quit)
        
        # 添加最近文件项
        for i, recent in enumerate(recent_sources):
            source = recent["source"]
            mode = recent["mode"]
            
            # 创建显示名称
            if len(source) > 30:
                display_name = source[:27] + "..."
            else:
                display_name = source
            
            self.recent_menu.add_command(
                label=f"{i+1}. {display_name}",
                command=lambda s=source, m=mode: self.load_recent_source(s, m)
            )
    
    def load_recent_source(self, source, mode):
        """加载最近使用的源文件/URL"""
        self.mode_var.set(mode)
        self.source_var.set(source)
        self.on_mode_change()
        
        # 如果是文件夹模式，加载文件夹结构
        if mode == "folder" and os.path.exists(source):
            self.load_folder_structure(source)
        
        self.log(f"已加载最近使用的源: {source}")
    
    def run(self):
        """运行应用程序"""
        # 加载最近使用的源文件
        self.load_recent_sources()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.mainloop()
    
    def on_closing(self):
        """窗口关闭事件处理"""
        # 保存用户配置
        self.save_user_config()
        self.root.quit()

if __name__ == "__main__":
    app = WebPackager()
    app.run()