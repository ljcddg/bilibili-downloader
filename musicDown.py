import requests
import os
import urllib3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from moviepy import VideoFileClip, AudioFileClip
from datetime import datetime

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BilibiliDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("B站视频下载工具")
        self.root.geometry("900x750")
        self.root.resizable(True, True)

        # 设置窗口背景色为天蓝色
        self.root.configure(bg='#E0F7FA')

        # 取消标志（用于中断下载）
        self.cancel_flag = False

        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')

        # 配置自定义样式 - 粉色和天蓝色主题
        style.configure('Title.TLabel',
                       font=('微软雅黑', 14, 'bold'),
                       foreground='#FF69B4',  # 热粉色
                       background='#E0F7FA')  # 天蓝色背景

        style.configure('Normal.TLabel',
                       font=('微软雅黑', 10),
                       foreground='#5D4037',  # 深棕色文字
                       background='#E0F7FA')  # 天蓝色背景

        style.configure('Action.TButton',
                       font=('微软雅黑', 10, 'bold'),
                       foreground='white',
                       background='#FFB6C1',  # 浅粉色按钮
                       padding=10)

        style.map('Action.TButton',
                 background=[('active', '#FF69B4'),  # 悬停时热粉色
                           ('disabled', '#FFD1DC')])  # 禁用时更浅的粉色

        style.configure('Cancel.TButton',
                       font=('微软雅黑', 10, 'bold'),
                       foreground='white',
                       background='#87CEEB',  # 天蓝色按钮
                       padding=10)

        style.map('Cancel.TButton',
                 background=[('active', '#5DADE2'),  # 悬停时深天蓝
                           ('disabled', '#B0E0E6')])  # 禁用时粉蓝色

        # 配置 Entry 样式 - 白色背景
        style.configure('Custom.TEntry',
                       fieldbackground='white',
                       foreground='#5D4037',
                       padding=5)

        # 配置 Progressbar 样式 - 粉色进度条
        style.configure('Pink.Horizontal.TProgressbar',
                       troughcolor='#FFE4E1',  # 浅粉色槽
                       background='#FF69B4',   # 粉色进度
                       thickness=20)

        # 配置 Frame 样式
        style.configure('Pink.TFrame',
                       background='#FFF0F5')  # 淡粉色框架

        style.configure('Blue.TFrame',
                       background='#E0F7FA')  # 天蓝色框架

        # 创建主框架 - 直接在天蓝色背景上，去掉外层粉色边框
        main_frame = ttk.Frame(root, padding="15", style='Blue.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # ===== 标题 =====
        title_label = ttk.Label(main_frame, text="🎬 B站视频下载工具", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # ===== 视频 URL 输入 =====
        video_label = ttk.Label(main_frame, text="📹 视频流 URL:", style='Normal.TLabel')
        video_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.video_url_var = tk.StringVar()
        video_entry = ttk.Entry(main_frame, textvariable=self.video_url_var, width=50, style='Custom.TEntry')
        video_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        video_paste_btn = ttk.Button(main_frame, text="📋 粘贴", command=self.paste_video_url, style='Action.TButton')
        video_paste_btn.grid(row=1, column=2, pady=5)

        # ===== 音频 URL 输入 =====
        audio_label = ttk.Label(main_frame, text="🎵 音频流 URL:", style='Normal.TLabel')
        audio_label.grid(row=2, column=0, sticky=tk.W, pady=5)

        self.audio_url_var = tk.StringVar()
        audio_entry = ttk.Entry(main_frame, textvariable=self.audio_url_var, width=50, style='Custom.TEntry')
        audio_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        audio_paste_btn = ttk.Button(main_frame, text="📋 粘贴", command=self.paste_audio_url, style='Action.TButton')
        audio_paste_btn.grid(row=2, column=2, pady=5)

        # ===== 帮助按钮 =====
        help_frame = ttk.Frame(main_frame, style='Blue.TFrame')
        help_frame.grid(row=3, column=0, columnspan=3, pady=5)
        
        help_btn = ttk.Button(help_frame, text="💡 如何获取URL？点击复制提示语", 
                             command=self.copy_help_text, style='Action.TButton')
        help_btn.pack(side=tk.LEFT, padx=5)

        # ===== 下载路径选择 =====
        path_label = ttk.Label(main_frame, text="📁 下载路径:", style='Normal.TLabel')
        path_label.grid(row=4, column=0, sticky=tk.W, pady=5)

        self.download_path_var = tk.StringVar(value=os.getcwd())
        path_entry = ttk.Entry(main_frame, textvariable=self.download_path_var, width=50, style='Custom.TEntry')
        path_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        browse_btn = ttk.Button(main_frame, text="📂 浏览...", command=self.browse_folder, style='Action.TButton')
        browse_btn.grid(row=4, column=2, pady=5)

        # ===== 自动合并选项 =====
        self.merge_var = tk.BooleanVar(value=True)
        merge_check = tk.Checkbutton(main_frame, text="勾选后自动视频合成",
                                     variable=self.merge_var,
                                     font=('微软雅黑', 10),
                                     bg='#E0F7FA',
                                     fg='#5D4037',
                                     activebackground='#E0F7FA',
                                     selectcolor='#E0F7FA',
                                     cursor='hand2')
        merge_check.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=5)

        # ===== 分隔线 =====
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)

        # ===== 下载按钮和取消按钮 =====
        btn_frame = ttk.Frame(main_frame, style='Blue.TFrame')
        btn_frame.grid(row=7, column=0, columnspan=3, pady=15)

        self.download_btn = ttk.Button(btn_frame, text="🚀 开始下载", command=self.start_download, style='Action.TButton')
        self.download_btn.pack(side=tk.LEFT, padx=10)

        self.cancel_btn = ttk.Button(btn_frame, text="❌ 取消下载", command=self.cancel_download, style='Cancel.TButton', state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=10)

        # ===== 进度条 =====
        progress_frame = ttk.Frame(main_frame, style='Blue.TFrame')
        progress_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100,
                                           style='Pink.Horizontal.TProgressbar')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        self.status_label = ttk.Label(progress_frame, text="✨ 就绪", style='Normal.TLabel')
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        # ===== 日志文本框 =====
        log_label = ttk.Label(main_frame, text="📝 下载日志:", style='Normal.TLabel')
        log_label.grid(row=9, column=0, sticky=tk.W, pady=(10, 5))

        log_frame = tk.Frame(main_frame, bg='#FFF0F5', highlightbackground='#FFB6C1', highlightthickness=2)
        log_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=18, wrap=tk.WORD, font=('Consolas', 9),
                               bg='white', fg='#5D4037', insertbackground='#FF69B4',
                               selectbackground='#FFB6C1', selectforeground='white')
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        main_frame.rowconfigure(10, weight=1)

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 添加提示
        self.log("💕 欢迎使用 B站视频下载工具！")
        self.log("💡 提示：URL 可以从浏览器开发者工具的 Network 标签中获取")
        self.log("💡 提示：筛选 .m4s 文件，找到视频流和音频流的请求")

    def copy_help_text(self):
        """复制帮助文本到剪贴板"""
        help_text = "帮我获取此页面最高清晰度AVC格式视频和音频的链接"
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(help_text)
            self.root.update()
            self.log(f"✅ 已复制提示语到剪贴板：{help_text}")
            messagebox.showinfo("成功", f"✅ 已复制到剪贴板！\n\n{help_text}\n\n您可以将此消息发送给AI助手获取URL")
        except Exception as e:
            self.log(f"❌ 复制失败: {str(e)}")
            messagebox.showerror("错误", f"复制失败: {str(e)}")

    def log(self, message):
        """在日志框中添加消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def paste_video_url(self):
        """粘贴视频 URL"""
        try:
            url = self.root.clipboard_get()
            self.video_url_var.set(url)
            self.log("✅ 已粘贴视频 URL")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴失败: {str(e)}")

    def paste_audio_url(self):
        """粘贴音频 URL"""
        try:
            url = self.root.clipboard_get()
            self.audio_url_var.set(url)
            self.log("✅ 已粘贴音频 URL")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴失败: {str(e)}")

    def browse_folder(self):
        """选择下载文件夹"""
        folder = filedialog.askdirectory(title="选择下载路径")
        if folder:
            self.download_path_var.set(folder)
            self.log(f"📁 下载路径: {folder}")

    def validate_inputs(self):
        """验证输入"""
        video_url = self.video_url_var.get().strip()
        audio_url = self.audio_url_var.get().strip()
        download_path = self.download_path_var.get().strip()

        if not video_url and not audio_url:
            messagebox.showwarning("警告", "请至少输入视频流 URL 或音频流 URL")
            return False

        if not download_path:
            messagebox.showwarning("警告", "请选择下载路径")
            return False

        if not os.path.exists(download_path):
            messagebox.showerror("错误", "下载路径不存在")
            return False

        # 如果勾选了合并，必须同时提供视频和音频
        if self.merge_var.get():
            if not video_url:
                messagebox.showwarning("警告", "勾选自动合成后，必须输入视频流 URL")
                return False
            if not audio_url:
                messagebox.showwarning("警告", "勾选自动合成后，必须输入音频流 URL")
                return False

        return True

    def cancel_download(self):
        """取消下载"""
        if messagebox.askyesno("确认", "确定要取消下载吗？\n未完成的文件将被删除。"):
            self.cancel_flag = True
            self.log("⚠️ 用户取消下载...")
            self.status_label.config(text="正在取消...")
            self.cancel_btn.config(state=tk.DISABLED)

    def on_closing(self):
        """处理窗口关闭事件"""
        # 检查是否正在下载
        if self.cancel_btn.cget('state') == tk.DISABLED and self.progress_var.get() > 0 and self.progress_var.get() < 100:
            if messagebox.askyesno("确认", "下载正在进行中，确定要关闭吗？\n未完成的文件将被删除。"):
                self.cancel_flag = True
                self.root.destroy()
        else:
            self.root.destroy()

    def download_file(self, url, filename, file_type):
        """下载单个文件"""
        try:
            self.log(f"📥 开始下载 {file_type}...")

            headers = {
                "referer": "https://www.bilibili.com",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            response = requests.get(url=url, headers=headers, timeout=60, verify=False, stream=True)

            if response.status_code != 200:
                self.log(f"❌ {file_type}下载失败！状态码: {response.status_code}")
                return False

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            filepath = os.path.join(self.download_path_var.get(), filename)

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # 检查是否取消
                    if self.cancel_flag:
                        self.log(f"⚠️ {file_type}下载已取消")
                        f.close()
                        # 删除未完成的文件
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            self.log(f"🗑️ 已删除未完成文件: {filename}")
                        return False

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.progress_var.set(progress)
                            self.status_label.config(text=f"下载 {file_type}: {progress:.1f}% ({downloaded/1024/1024:.1f} MB)")

            self.log(f"✅ {file_type}下载完成！大小: {downloaded/1024/1024:.2f} MB")
            self.log(f"📁 保存位置: {filepath}")
            return True

        except Exception as e:
            self.log(f"❌ {file_type}下载出错: {str(e)}")
            return False

    def merge_video_audio(self, video_path, audio_path, output_path):
        """合并视频和音频文件"""
        print("\n" + "="*60)
        print("🔍 [DEBUG] 开始音视频合并诊断")
        print("="*60)
        
        try:
            self.log("🎬 开始合并视频和音频...")
            self.status_label.config(text="🎬 正在合并音视频...")
            
            # 检查文件是否存在
            print(f"\n[1] 检查文件存在性:")
            print(f"   视频路径: {video_path}")
            print(f"   音频路径: {audio_path}")
            
            if not os.path.exists(video_path):
                error_msg = f"❌ 视频文件不存在: {video_path}"
                print(f"   {error_msg}")
                self.log(error_msg)
                return False
            else:
                print(f"   ✅ 视频文件存在")
            
            if not os.path.exists(audio_path):
                error_msg = f"❌ 音频文件不存在: {audio_path}"
                print(f"   {error_msg}")
                self.log(error_msg)
                return False
            else:
                print(f"   ✅ 音频文件存在")
            
            # 检查文件大小
            print(f"\n[2] 检查文件大小:")
            video_size = os.path.getsize(video_path)
            audio_size = os.path.getsize(audio_path)
            print(f"   视频大小: {video_size} bytes ({video_size / 1024 / 1024:.2f} MB)")
            print(f"   音频大小: {audio_size} bytes ({audio_size / 1024 / 1024:.2f} MB)")
            
            self.log(f"📊 视频文件大小: {video_size / 1024 / 1024:.2f} MB")
            self.log(f"📊 音频文件大小: {audio_size / 1024 / 1024:.2f} MB")
            
            if video_size == 0:
                error_msg = "❌ 视频文件为空 (0 bytes)"
                print(f"   {error_msg}")
                self.log(error_msg)
                return False
            
            if audio_size == 0:
                error_msg = "❌ 音频文件为空 (0 bytes)"
                print(f"   {error_msg}")
                self.log(error_msg)
                return False
            
            print(f"   ✅ 文件大小正常")
            
            # 加载视频和音频
            print(f"\n[3] 加载视频文件:")
            self.log("📂 正在加载视频文件...")
            print(f"   尝试加载: {video_path}")
            try:
                video_clip = VideoFileClip(video_path)
                print(f"   ✅ 视频加载成功")
                print(f"   - 时长: {video_clip.duration:.2f} 秒")
                print(f"   - 尺寸: {video_clip.size}")
                print(f"   - FPS: {video_clip.fps}")
                print(f"   - 是否有音频轨道: {video_clip.audio is not None}")
                self.log(f"✅ 视频加载成功 - 时长: {video_clip.duration:.2f}秒, 尺寸: {video_clip.size}")
            except Exception as e:
                error_msg = f"❌ 视频加载失败: {str(e)}"
                print(f"   {error_msg}")
                self.log(error_msg)
                import traceback
                print(f"   错误堆栈:\n{traceback.format_exc()}")
                self.log("💡 提示: B站的视频流可能是特殊编码格式，MoviePy 无法直接处理")
                self.log("💡 建议: 使用 FFmpeg 或其他工具手动合并")
                return False
            
            print(f"\n[4] 加载音频文件:")
            self.log("📂 正在加载音频文件...")
            print(f"   尝试加载: {audio_path}")
            try:
                audio_clip = AudioFileClip(audio_path)
                print(f"   ✅ 音频加载成功")
                print(f"   - 时长: {audio_clip.duration:.2f} 秒")
                print(f"   - 采样率: {audio_clip.fps if hasattr(audio_clip, 'fps') else 'N/A'} Hz")
                self.log(f"✅ 音频加载成功 - 时长: {audio_clip.duration:.2f}秒")
            except Exception as e:
                error_msg = f"❌ 音频加载失败: {str(e)}"
                print(f"   {error_msg}")
                self.log(error_msg)
                video_clip.close()
                import traceback
                print(f"   错误堆栈:\n{traceback.format_exc()}")
                self.log("💡 提示: B站的音频流可能是特殊编码格式，MoviePy 无法直接处理")
                return False
            
            # 检查时长差异
            print(f"\n[5] 检查时长匹配:")
            duration_diff = abs(video_clip.duration - audio_clip.duration)
            print(f"   视频时长: {video_clip.duration:.2f} 秒")
            print(f"   音频时长: {audio_clip.duration:.2f} 秒")
            print(f"   时长差异: {duration_diff:.2f} 秒")
            
            if duration_diff > 1:
                warning_msg = f"⚠️ 警告: 视频和音频时长差异较大 ({duration_diff:.2f}秒)"
                print(f"   {warning_msg}")
                self.log(warning_msg)
                
                if audio_clip.duration > video_clip.duration:
                    print(f"   ✂️ 裁剪音频以匹配视频时长...")
                    self.log("✂️ 裁剪音频以匹配视频时长...")
                    try:
                        audio_clip = audio_clip.with_duration(video_clip.duration)
                        print(f"   ✅ 音频裁剪成功，新时长: {audio_clip.duration:.2f} 秒")
                    except Exception as e:
                        error_msg = f"❌ 音频裁剪失败: {str(e)}"
                        print(f"   {error_msg}")
                        self.log(error_msg)
                        video_clip.close()
                        audio_clip.close()
                        return False
            else:
                print(f"   ✅ 时长匹配良好")
            
            # 合并音视频
            print(f"\n[6] 合并音视频轨道:")
            self.log("🔧 正在合并音视频轨道...")
            try:
                final_clip = video_clip.with_audio(audio_clip)
                print(f"   ✅ 音轨合并成功")
                print(f"   - 最终时长: {final_clip.duration:.2f} 秒")
                print(f"   - 是否有音频: {final_clip.audio is not None}")
            except Exception as e:
                error_msg = f"❌ 音轨合并失败: {str(e)}"
                print(f"   {error_msg}")
                self.log(error_msg)
                video_clip.close()
                audio_clip.close()
                import traceback
                print(f"   错误堆栈:\n{traceback.format_exc()}")
                return False
            
            # 输出合并后的视频
            print(f"\n[7] 写入输出文件:")
            print(f"   输出路径: {output_path}")
            print(f"   编码格式: H.264 (视频) + AAC (音频)")
            self.log("💾 正在写入输出文件...")
            
            # 创建自定义进度回调
            total_duration = final_clip.duration
            start_time = threading.Event()
            
            def progress_callback(index, max_index):
                """实时进度回调函数"""
                if max_index > 0:
                    progress = (index / max_index) * 100
                    # 映射到 75-100% 的进度范围
                    mapped_progress = 75 + (progress / 100) * 25
                    self.progress_var.set(mapped_progress)
                    elapsed = index / max_index
                    status_text = f"🎬 合并进度: {progress:.1f}% ({index}/{max_index})"
                    self.status_label.config(text=status_text)
                    self.root.update_idletasks()
            
            try:
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    logger='bar',
                    preset='medium',
                    fps=video_clip.fps if video_clip.fps else 30
                )
                print(f"   ✅ 文件写入完成")
            except Exception as e:
                error_msg = f"❌ 文件写入失败: {str(e)}"
                print(f"   {error_msg}")
                self.log(error_msg)
                video_clip.close()
                audio_clip.close()
                final_clip.close()
                import traceback
                print(f"   错误堆栈:\n{traceback.format_exc()}")
                return False
            
            # 关闭资源
            print(f"\n[8] 释放资源:")
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            print(f"   ✅ 所有资源已释放")
            
            # 验证输出文件
            print(f"\n[9] 验证输出文件:")
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                success_msg = f"✅ 合并完成！文件大小: {output_size / 1024 / 1024:.2f} MB"
                print(f"   {success_msg}")
                print(f"   输出路径: {output_path}")
                self.log(success_msg)
                self.log(f"📁 输出文件: {output_path}")
                print("="*60)
                print("✅ [DEBUG] 合并成功完成")
                print("="*60 + "\n")
                return True
            else:
                error_msg = "❌ 合并后文件未生成"
                print(f"   {error_msg}")
                self.log(error_msg)
                print("="*60)
                print("❌ [DEBUG] 合并失败 - 输出文件不存在")
                print("="*60 + "\n")
                return False
            
        except Exception as e:
            error_msg = f"❌ 合并过程发生未知错误: {str(e)}"
            print(f"\n{error_msg}")
            self.log(error_msg)
            import traceback
            error_detail = traceback.format_exc()
            print(f"\n完整错误堆栈:")
            print(error_detail)
            self.log(f"📋 错误详情:")
            for line in error_detail.split('\n'):
                if line.strip():
                    self.log(f"   {line}")
            print("="*60)
            print("❌ [DEBUG] 合并失败 - 异常捕获")
            print("="*60 + "\n")
            return False

    def start_download(self):
        """开始下载（在新线程中执行）"""
        if not self.validate_inputs():
            return

        # 重置取消标志
        self.cancel_flag = False

        # 禁用下载按钮，启用取消按钮
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)

        # 重置进度
        self.progress_var.set(0)
        self.status_label.config(text="✨ 准备下载...")

        # 在新线程中执行下载
        thread = threading.Thread(target=self.download_task, daemon=True)
        thread.start()

    def download_task(self):
        """下载任务（在线程中执行）"""
        video_path = None
        audio_path = None
        output_path = None
        
        try:
            video_url = self.video_url_var.get().strip()
            audio_url = self.audio_url_var.get().strip()
            download_path = self.download_path_var.get().strip()

            # 生成带时间戳的文件名
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")

            self.log("=" * 50)
            self.log("💕 开始下载任务")
            self.log("=" * 50)

            # 判断下载模式
            has_video = bool(video_url)
            has_audio = bool(audio_url)
            
            if has_video and has_audio:
                self.log("📋 下载模式：视频 + 音频")
            elif has_video:
                self.log("📋 下载模式：仅视频")
            else:
                self.log("📋 下载模式：仅音频")

            # 下载视频
            if has_video:
                video_filename = f"视频_{timestamp}.mp4"
                self.log(f"📝 视频文件名: {video_filename}")
                video_success = self.download_file_with_name(video_url, video_filename, '视频')
                video_path = os.path.join(download_path, video_filename)

                # 检查是否被取消
                if self.cancel_flag:
                    self.log("⚠️ 下载已取消")
                    self.status_label.config(text="已取消")
                    self.enable_buttons()
                    return

                if not video_success:
                    self.log("⚠️ 视频下载失败")
                    if has_audio:
                        self.log("⚠️ 将继续下载音频...")
                    else:
                        self.enable_buttons()
                        return
            else:
                video_success = False
                self.log("ℹ️ 未提供视频URL，跳过视频下载")

            # 下载音频
            if has_audio:
                if has_video and video_success:
                    self.progress_var.set(50)
                    self.status_label.config(text="💕 视频下载完成，开始下载音频...")
                elif has_video and not video_success:
                    self.status_label.config(text="💕 视频下载失败，开始下载音频...")
                else:
                    self.status_label.config(text="💕 开始下载音频...")
                
                audio_filename = f"音频_{timestamp}.mp3"
                self.log(f"📝 音频文件名: {audio_filename}")
                audio_success = self.download_file_with_name(audio_url, audio_filename, '音频')
                audio_path = os.path.join(download_path, audio_filename)

                # 检查是否被取消
                if self.cancel_flag:
                    self.log("⚠️ 下载已取消")
                    self.status_label.config(text="已取消")
                    self.enable_buttons()
                    return

                if not audio_success:
                    self.log("⚠️ 音频下载失败")
                    if has_video and video_success:
                        self.status_label.config(text="⚠️ 音频下载失败，视频已保留")
                        messagebox.showwarning("警告", "视频下载成功，但音频下载失败")
                    else:
                        self.status_label.config(text="⚠️ 音频下载失败")
                    self.enable_buttons()
                    return
            else:
                audio_success = False
                self.log("ℹ️ 未提供音频URL，跳过音频下载")

            # 如果勾选了自动合并，则执行合并操作
            if self.merge_var.get() and video_success and audio_success:
                print(f"\n[DEBUG] 检查合并选项: self.merge_var.get() = {self.merge_var.get()}")
                self.log("✅ 检测到合并选项已勾选，开始执行合并...")
                self.progress_var.set(75)
                
                # 生成带时间戳的合并文件名
                output_filename = f"完整视频_{timestamp}.mp4"
                output_path = os.path.join(download_path, output_filename)
                
                self.log(f"📝 输出文件名: {output_filename}")
                merge_success = self.merge_video_audio(video_path, audio_path, output_path)

                if merge_success:
                    # 合并成功后删除临时文件
                    try:
                        if os.path.exists(video_path):
                            os.remove(video_path)
                            self.log(f"🗑️ 已删除临时视频文件: {video_filename}")
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                            self.log(f"🗑️ 已删除临时音频文件: {audio_filename}")
                    except Exception as e:
                        self.log(f"⚠️ 清理临时文件时出错: {str(e)}")

                    self.progress_var.set(100)
                    self.status_label.config(text="💕 下载并合并完成！")
                    self.log("=" * 50)
                    self.log("🎉 视频下载并合并完成！")
                    self.log(f"📂 最终文件位置: {output_path}")
                    messagebox.showinfo("成功", f"💕 视频下载并合并完成！\n\n文件名: {output_filename}\n\n临时文件已自动清理。\n只保留了合并后的完整视频。")
                else:
                    # 合并失败，保留原始文件
                    self.status_label.config(text="⚠️ 合并失败")
                    self.log("=" * 50)
                    self.log("⚠️ 合并失败，原始文件已保留")
                    self.log(f"📹 视频文件: {video_path}")
                    self.log(f"🎵 音频文件: {audio_path}")
                    messagebox.showerror("错误", 
                        f"❌ 视频和音频下载成功，但合并失败！\n\n"
                        f"原始文件已保留，您可以手动处理：\n"
                        f"• 视频: {video_path}\n"
                        f"• 音频: {audio_path}\n\n"
                        f"请查看日志了解详细错误信息。")
            else:
                # 未勾选合并或只有一个文件，显示下载结果
                self.progress_var.set(100)
                self.status_label.config(text="💕 下载完成！")
                self.log("=" * 50)
                self.log("🎉 下载完成！")
                
                if video_success and audio_success:
                    self.log(f"📹 视频文件: {video_path}")
                    self.log(f"🎵 音频文件: {audio_path}")
                    messagebox.showinfo("成功", 
                        f"💕 视频和音频下载完成！\n\n"
                        f"• 视频: {video_filename}\n"
                        f"• 音频: {audio_filename}\n\n"
                        f"提示：勾选'自动视频合成'可自动合并")
                elif video_success:
                    self.log(f"📹 视频文件: {video_path}")
                    messagebox.showinfo("成功", 
                        f"💕 视频下载完成！\n\n"
                        f"• 视频: {video_filename}")
                elif audio_success:
                    self.log(f"🎵 音频文件: {audio_path}")
                    messagebox.showinfo("成功", 
                        f"💕 音频下载完成！\n\n"
                        f"• 音频: {audio_filename}")
                
                self.log(f"📂 文件位置: {download_path}")

        except Exception as e:
            self.log(f"❌ 下载任务出错: {str(e)}")
            import traceback
            self.log(f"📋 错误堆栈:\n{traceback.format_exc()}")
            messagebox.showerror("错误", f"下载失败: {str(e)}")

        finally:
            self.enable_buttons()

    def download_file_with_name(self, url, filename, file_type):
        """下载单个文件（使用指定文件名）"""
        try:
            self.log(f"📥 开始下载 {file_type}...")

            headers = {
                "referer": "https://www.bilibili.com",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            response = requests.get(url=url, headers=headers, timeout=60, verify=False, stream=True)

            if response.status_code != 200:
                self.log(f"❌ {file_type}下载失败！状态码: {response.status_code}")
                return False

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            filepath = os.path.join(self.download_path_var.get(), filename)

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # 检查是否取消
                    if self.cancel_flag:
                        self.log(f"⚠️ {file_type}下载已取消")
                        f.close()
                        # 删除未完成的文件
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            self.log(f"🗑️ 已删除未完成文件: {filename}")
                        return False

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.progress_var.set(progress)
                            self.status_label.config(text=f"下载 {file_type}: {progress:.1f}% ({downloaded/1024/1024:.1f} MB)")

            self.log(f"✅ {file_type}下载完成！大小: {downloaded/1024/1024:.2f} MB")
            self.log(f"📁 保存位置: {filepath}")
            return True

        except Exception as e:
            self.log(f"❌ {file_type}下载出错: {str(e)}")
            return False

    def enable_buttons(self):
        """启用按钮"""
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = BilibiliDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
