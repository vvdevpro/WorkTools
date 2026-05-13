import os
import sys
import json
import random
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ================= [系统路径配置] =================
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
TIME_OUTPUT_DIR = os.path.join(BASE_DIR, "已加时间地点水印")
ANTI_THEFT_OUTPUT_DIR = os.path.join(BASE_DIR, "已加防盗水印")
COMPRESS_OUTPUT_DIR = os.path.join(BASE_DIR, "已压缩结果")

FONT_PATH = "C:\\Windows\\Fonts\\msyh.ttc"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "C:\\Windows\\Fonts\\simhei.ttf"


# ================= [配置管理] =================
def load_config():
    default_config = {
        "start_time": "09:51",
        "date_text": "2026-04-16 星期四",
        "location_text": "重庆市·gay佬转转转酒吧",
        "dynamic_time": True,
        "anti_theft_text": "防盗水印文字",
        "anti_theft_alpha": 100,
        "compress_kb": 100,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except:
            pass
    return default_config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


# ================= [图片处理通用工具] =================
def get_images_in_dir():
    valid_exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(valid_exts)]
    return files


def get_real_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_sharp_text(
    draw, x, y, text, font, fill_color=(255, 255, 255), stroke_color=(0, 0, 0)
):
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill_color,
        stroke_width=1,
        stroke_fill=stroke_color,
    )


# ================= [核心逻辑 1：时间地点水印] =================
def process_time_watermark(config):
    files = get_images_in_dir()
    if not files:
        messagebox.showwarning("警告", f"当前目录 ({BASE_DIR}) 下没有找到图片！")
        return

    if not os.path.exists(TIME_OUTPUT_DIR):
        os.makedirs(TIME_OUTPUT_DIR)

    start_time_str = config.get("start_time", "")
    draw_time = bool(start_time_str)
    current_time = None
    if draw_time:
        try:
            current_time = datetime.strptime(start_time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("错误", "时间格式错误，请使用 09:51 这种格式！")
            return

    success_count = 0
    for filename in files:
        TIME_TEXT = current_time.strftime("%H:%M") if draw_time else ""
        input_path = os.path.join(BASE_DIR, filename)
        output_path = os.path.join(TIME_OUTPUT_DIR, filename)

        try:
            with Image.open(input_path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                draw = ImageDraw.Draw(img)
                width, height = img.size
                base_size = min(width, height)

                big_font = ImageFont.truetype(FONT_PATH, int(base_size * 0.15))
                small_font = ImageFont.truetype(FONT_PATH, int(base_size * 0.038))

                y_time = height * 0.75 if height > width else height * 0.70
                h_time = 0

                if draw_time:
                    w_time, h_time = get_real_size(draw, TIME_TEXT, big_font)
                    x_time = (width - w_time) / 2
                    draw_sharp_text(draw, x_time, y_time, TIME_TEXT, big_font)

                spacing = int(base_size * 0.05) if draw_time else 0
                y_small = y_time + h_time + spacing if draw_time else height * 0.82

                DATE_TEXT = config.get("date_text", "")
                LOC_TEXT = config.get("location_text", "")

                if DATE_TEXT and LOC_TEXT:
                    w_date, h_date = get_real_size(draw, DATE_TEXT, small_font)
                    w_loc, _ = get_real_size(draw, LOC_TEXT, small_font)
                    dot_radius = int(base_size * 0.006)
                    pad = int(base_size * 0.01)
                    total_w = w_date + pad + (dot_radius * 2) + pad + w_loc
                    x_start = (width - total_w) / 2
                    draw_sharp_text(draw, x_start, y_small, DATE_TEXT, small_font)
                    x_dot = x_start + w_date + pad
                    y_dot = y_small + (h_date / 2) - dot_radius + (base_size * 0.005)
                    draw.ellipse(
                        [x_dot, y_dot, x_dot + dot_radius * 2, y_dot + dot_radius * 2],
                        fill=(235, 60, 60),
                        outline=(0, 0, 0),
                        width=1,
                    )
                    draw_sharp_text(
                        draw,
                        x_dot + (dot_radius * 2) + pad,
                        y_small,
                        LOC_TEXT,
                        small_font,
                    )
                elif DATE_TEXT:
                    w_date, _ = get_real_size(draw, DATE_TEXT, small_font)
                    draw_sharp_text(
                        draw, (width - w_date) / 2, y_small, DATE_TEXT, small_font
                    )
                elif LOC_TEXT:
                    w_loc, _ = get_real_size(draw, LOC_TEXT, small_font)
                    draw_sharp_text(
                        draw, (width - w_loc) / 2, y_small, LOC_TEXT, small_font
                    )

                img.save(output_path, quality=95)
                success_count += 1

        except Exception as e:
            print(f"处理 {filename} 失败: {e}")

        if draw_time and config.get("dynamic_time", True):
            current_time += timedelta(minutes=random.randint(1, 4))

    messagebox.showinfo(
        "完成", f"时间地点水印处理完毕！\n共成功处理 {success_count} 张图片。"
    )


# ================= [核心逻辑 2：防盗水印] =================
def process_anti_theft_watermark(config):
    files = get_images_in_dir()
    if not files:
        messagebox.showwarning("警告", f"当前目录 ({BASE_DIR}) 下没有找到图片！")
        return

    if not os.path.exists(ANTI_THEFT_OUTPUT_DIR):
        os.makedirs(ANTI_THEFT_OUTPUT_DIR)

    text = config.get("anti_theft_text", "内部文件 请勿外传")
    if not text:
        messagebox.showerror("错误", "防盗水印内容不能为空！")
        return

    try:
        alpha = int(config.get("anti_theft_alpha", 100))
    except:
        alpha = 100

    success_count = 0
    for filename in files:
        input_path = os.path.join(BASE_DIR, filename)
        output_path = os.path.join(ANTI_THEFT_OUTPUT_DIR, filename)

        try:
            with Image.open(input_path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode != "RGBA":
                    img = img.convert("RGBA")

                width, height = img.size
                base_size = min(width, height)

                big_font = ImageFont.truetype(FONT_PATH, int(base_size * 0.05))
                small_font = ImageFont.truetype(FONT_PATH, int(base_size * 0.04))

                temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
                w_big, h_big = get_real_size(temp_draw, text, big_font)
                w_small, h_small = get_real_size(temp_draw, text, small_font)

                x_spacing = w_small + int(base_size * 0.35)
                y_spacing = h_small + int(base_size * 0.35)

                diagonal = int((width**2 + height**2) ** 0.5)
                layer_size = (diagonal, diagonal)
                wm_layer = Image.new("RGBA", layer_size, (255, 255, 255, 0))
                wm_draw = ImageDraw.Draw(wm_layer)

                center_x = layer_size[0] // 2
                center_y = layer_size[1] // 2

                fill_color_small = (200, 200, 200, alpha)
                for y in range(0, layer_size[1], y_spacing):
                    for x in range(0, layer_size[0], x_spacing):
                        offset_x = (
                            x if (y // y_spacing) % 2 == 0 else x - (x_spacing // 2)
                        )
                        if abs(offset_x + w_small / 2 - center_x) < (
                            w_big * 0.5 + base_size * 0.1
                        ) and abs(y + h_small / 2 - center_y) < (
                            h_big * 0.5 + base_size * 0.15
                        ):
                            continue
                        wm_draw.text(
                            (offset_x, y), text, font=small_font, fill=fill_color_small
                        )

                big_x = center_x - (w_big / 2)
                big_y = center_y - (h_big / 2)
                draw_sharp_text(
                    wm_draw,
                    big_x,
                    big_y,
                    text,
                    big_font,
                    fill_color=(255, 255, 255, alpha),
                    stroke_color=(0, 0, 0, alpha),
                )

                rotated_wm = wm_layer.rotate(45, expand=0)

                paste_x = (width - layer_size[0]) // 2
                paste_y = (height - layer_size[1]) // 2
                img.alpha_composite(rotated_wm, (paste_x, paste_y))

                img = img.convert("RGB")
                img.save(output_path, quality=95)
                success_count += 1

        except Exception as e:
            print(f"处理 {filename} 失败: {e}")

    messagebox.showinfo(
        "完成", f"防盗水印处理完毕！\n共成功处理 {success_count} 张图片。"
    )


# ================= [核心逻辑 3：图片批量压缩] =================
def compress_image_to_target(input_path, output_path, target_kb):
    img = Image.open(input_path)

    max_size = 1920
    if max(img.width, img.height) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    low, high = 10, 95
    best_quality = 10

    img.save(output_path, "JPEG", optimize=True, quality=high, subsampling=0)
    if os.path.getsize(output_path) / 1024 <= target_kb:
        return True, high

    while low <= high:
        mid = (low + high) // 2
        img.save(output_path, "JPEG", optimize=True, quality=mid, subsampling=0)
        size_kb = os.path.getsize(output_path) / 1024

        if size_kb <= target_kb:
            best_quality = mid
            low = mid + 1
        else:
            high = mid - 1

    img.save(output_path, "JPEG", optimize=True, quality=best_quality, subsampling=0)
    return True, best_quality


def process_compression(config):
    files = get_images_in_dir()
    if not files:
        messagebox.showwarning("警告", f"当前目录 ({BASE_DIR}) 下没有找到图片！")
        return

    if not os.path.exists(COMPRESS_OUTPUT_DIR):
        os.makedirs(COMPRESS_OUTPUT_DIR)

    try:
        target_kb = float(config.get("compress_kb", 100))
    except ValueError:
        messagebox.showerror("错误", "压缩目标大小必须是数字！")
        return

    success_count = 0
    for filename in files:
        input_path = os.path.join(BASE_DIR, filename)
        output_filename = os.path.splitext(filename)[0] + "_已压缩.jpg"
        output_path = os.path.join(COMPRESS_OUTPUT_DIR, output_filename)

        try:
            compress_image_to_target(input_path, output_path, target_kb)
            success_count += 1
        except Exception as e:
            print(f"处理 {filename} 失败: {e}")

    messagebox.showinfo(
        "完成", f"批量压缩处理完毕！\n共成功压缩 {success_count} 张图片。"
    )


# ================= [GUI 界面构建] =================
class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片处理全能助手 v3.0")
        self.root.geometry("380x300")
        self.root.resizable(False, False)

        self.config = load_config()
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TButton", font=("Microsoft YaHei", 12), padding=8)

        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        lbl_title = ttk.Label(
            main_frame,
            text="请选择要执行的操作：",
            font=("Microsoft YaHei", 12, "bold"),
        )
        lbl_title.pack(pady=(0, 15))

        btn_time = ttk.Button(
            main_frame, text="📍 添加 时间/地点水印", command=self.open_time_config
        )
        btn_time.pack(fill=tk.X, pady=6)

        btn_anti = ttk.Button(
            main_frame, text="🛡️ 添加 满屏防盗水印", command=self.open_anti_config
        )
        btn_anti.pack(fill=tk.X, pady=6)

        btn_compress = ttk.Button(
            main_frame, text="🗜️ 批量 无损图片压缩", command=self.open_compress_config
        )
        btn_compress.pack(fill=tk.X, pady=6)

        lbl_tips = ttk.Label(
            main_frame,
            text="提示: 请将本程序与要处理的图片放在同一文件夹",
            font=("Microsoft YaHei", 9),
            foreground="gray",
        )
        lbl_tips.pack(side=tk.BOTTOM, pady=5)

    # ------ 时间地点配置窗口 ------
    def open_time_config(self):
        top = tk.Toplevel(self.root)
        top.title("时间地点配置")
        top.geometry("350x260")
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()

        ttk.Label(top, text="初始时间 (如 09:51):").grid(
            row=0, column=0, padx=15, pady=15, sticky=tk.W
        )
        entry_time = ttk.Entry(top, width=20)
        entry_time.grid(row=0, column=1, padx=10, pady=15)
        entry_time.insert(0, self.config.get("start_time", ""))

        ttk.Label(top, text="日期:").grid(
            row=1, column=0, padx=15, pady=10, sticky=tk.W
        )
        entry_date = ttk.Entry(top, width=20)
        entry_date.grid(row=1, column=1, padx=10, pady=10)
        entry_date.insert(0, self.config.get("date_text", ""))

        ttk.Label(top, text="地点:").grid(
            row=2, column=0, padx=15, pady=10, sticky=tk.W
        )
        entry_loc = ttk.Entry(top, width=20)
        entry_loc.grid(row=2, column=1, padx=10, pady=10)
        entry_loc.insert(0, self.config.get("location_text", ""))

        var_dynamic = tk.BooleanVar(value=self.config.get("dynamic_time", True))
        chk_dynamic = ttk.Checkbutton(
            top, text="开启时间动态随机增加 (1-4分钟)", variable=var_dynamic
        )
        chk_dynamic.grid(row=3, column=0, columnspan=2, padx=15, pady=10, sticky=tk.W)

        def save_and_run():
            self.config["start_time"] = entry_time.get().strip()
            self.config["date_text"] = entry_date.get().strip()
            self.config["location_text"] = entry_loc.get().strip()
            self.config["dynamic_time"] = var_dynamic.get()
            save_config(self.config)
            top.destroy()
            process_time_watermark(self.config)

        ttk.Button(top, text="保存并开始处理", command=save_and_run).grid(
            row=4, column=0, columnspan=2, pady=15
        )

    # ------ 防盗水印配置窗口 ------
    def open_anti_config(self):
        top = tk.Toplevel(self.root)
        top.title("防盗水印配置")
        top.geometry("350x200")
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()

        ttk.Label(top, text="防盗水印文字:").grid(
            row=0, column=0, padx=15, pady=20, sticky=tk.W
        )
        entry_text = ttk.Entry(top, width=20)
        entry_text.grid(row=0, column=1, padx=10, pady=20)
        entry_text.insert(
            0,
            self.config.get(
                "anti_theft_text",
                "防盗水印",
            ),
        )

        ttk.Label(top, text="不透明度 (0-255):").grid(
            row=1, column=0, padx=15, pady=10, sticky=tk.W
        )
        scale_alpha = tk.Scale(top, from_=10, to=255, orient=tk.HORIZONTAL, length=140)
        scale_alpha.set(self.config.get("anti_theft_alpha", 100))
        scale_alpha.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        def save_and_run():
            self.config["anti_theft_text"] = entry_text.get().strip()
            self.config["anti_theft_alpha"] = scale_alpha.get()
            save_config(self.config)
            top.destroy()
            process_anti_theft_watermark(self.config)

        ttk.Button(top, text="保存并开始处理", command=save_and_run).grid(
            row=2, column=0, columnspan=2, pady=20
        )

    # ------ 批量压缩配置窗口 ------
    def open_compress_config(self):
        top = tk.Toplevel(self.root)
        top.title("图片压缩配置")
        top.geometry("320x150")
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()

        ttk.Label(top, text="限制最大体积 (KB):").grid(
            row=0, column=0, padx=15, pady=30, sticky=tk.W
        )
        entry_kb = ttk.Entry(top, width=15)
        entry_kb.grid(row=0, column=1, padx=10, pady=30)
        entry_kb.insert(0, str(self.config.get("compress_kb", 100)))

        def save_and_run():
            try:
                kb_val = float(entry_kb.get().strip())
                if kb_val <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("错误", "请输入有效的大于0的数字！")
                return

            self.config["compress_kb"] = kb_val
            save_config(self.config)
            top.destroy()
            process_compression(self.config)

        ttk.Button(top, text="保存并开始处理", command=save_and_run).grid(
            row=1, column=0, columnspan=2, pady=5
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkApp(root)

    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2
    root.geometry("+%d+%d" % (x, y))

    root.mainloop()
