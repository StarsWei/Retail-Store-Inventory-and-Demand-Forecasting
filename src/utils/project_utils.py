import os
import time
import psutil
import traceback
import pandas as pd
from datetime import datetime

class ProjectUtils:
    def __init__(self, project_root=None, log_prefix="log", enable_csv=True):
        """
        初始化项目工具
        功能：
        1. 自动获取项目根目录
        2. 日志记录到 logs/
        3. 可选生成结构化 CSV 日志
        """
        # 自动识别项目根目录
        if project_root is None:
            project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
        self.project_root = project_root

        # logs目录
        self.log_dir = os.path.join(self.project_root, "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        # 日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_prefix = log_prefix
        self.log_file = os.path.join(self.log_dir, f"{log_prefix}_{timestamp}.log")
        self.csv_file = os.path.join(self.log_dir, f"{log_prefix}_summary.csv") if enable_csv else None

        # 性能监控
        self.start_time = None
        self.process = psutil.Process(os.getpid())

        # 初始化 CSV
        if enable_csv and not os.path.exists(self.csv_file):
            pd.DataFrame(columns=[
                "task_name", "start_time", "duration_sec", "cpu_percent", "mem_usage_mb", "status", "error_message"
            ]).to_csv(self.csv_file, index=False, encoding="utf-8-sig")

        self.log("🚀 项目工具初始化成功")

    # --- 日志记录 ---
    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # --- 开始计时 ---
    def start_timer(self):
        self.start_time = time.time()
        self.log("⏱️ 任务计时开始")

    # --- 结束计时并写入性能日志 ---
    def end_timer(self, task_name="unknown", status="success", error_message=None):
        if self.start_time is None:
            self.log("⚠️ 未调用 start_timer()，无法计算运行时间")
            return
        duration = time.time() - self.start_time
        cpu_percent = psutil.cpu_percent(interval=1)
        mem_usage_mb = self.process.memory_info().rss / 1024 / 1024

        self.log(f"⏱️ 总耗时: {duration:.2f} 秒")
        self.log(f"💻 CPU使用率: {cpu_percent:.1f}%")
        self.log(f"🧠 内存占用: {mem_usage_mb:.2f} MB")

        # 写入 CSV
        if self.csv_file:
            new_entry = pd.DataFrame([{
                "task_name": task_name,
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_sec": round(duration, 2),
                "cpu_percent": cpu_percent,
                "mem_usage_mb": round(mem_usage_mb, 2),
                "status": status,
                "error_message": error_message if error_message else ""
            }])
            existing = pd.read_csv(self.csv_file)
            pd.concat([existing, new_entry], ignore_index=True).to_csv(
                self.csv_file, index=False, encoding="utf-8-sig"
            )

    # --- 异常记录 ---
    def exception(self, e, task_name="unknown"):
        self.log("❌ 出现错误：")
        error_msg = traceback.format_exc()
        self.log(error_msg)
        self.end_timer(task_name=task_name, status="failed", error_message=error_msg)

    # --- 获取数据路径 ---
    def data_path(self, *args):
        """
        获取项目 data 文件夹路径，支持多层子目录
        用法：
        utils.data_path("processed", "retail_data_clean.csv")
        """
        path = os.path.join(self.project_root, "data", *args)
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ 数据文件不存在：{path}")
        return path
