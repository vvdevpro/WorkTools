#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动化 PDF 智能提取工具 (生产环境高可用版)

优化特性:
    1. 交互增强：完善的输入引导与防呆校验。
    2. 极速并发：基于 Pool Initializer 的模型池化，彻底解决重复加载模型的资源浪费。
    3. 负载均衡：采用“页级 (Page-level)”任务切分，防止超大单文件阻塞进程，进度条更精准。
    4. 健壮容错：三级异常捕获 (进程、文件、页面)，确保残缺或损坏的 PDF 不会导致整个任务崩溃。
"""

__author__ = "vv"
__version__ = "5.1.0"
__date__ = "2026-04-21"
__license__ = "MIT"

import os
import sys

# =====================================================================
# 核心压制：必须在导入任何第三方库之前，锁死底层计算库的线程池！
# =====================================================================
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import time
import multiprocessing
import concurrent.futures
from collections import defaultdict
from typing import List, Tuple, Dict

# =====================================================================
# 子进程初始化：保障每个进程生命周期内只加载一次 AI 模型
# =====================================================================
def init_worker():
    """初始化子进程环境与 OCR 引擎"""

    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)

    global ocr_engine
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr_engine = RapidOCR()
    except Exception as e:
        print(f"\n[致命错误] 子进程 OCR 模型初始化失败: {e}")
        sys.exit(1)

    # 优雅降级：降低子进程优先级，保证电脑前台操作不卡顿
    import psutil
    try:
        p = psutil.Process(os.getpid())
        if sys.platform == 'win32':
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            p.nice(10)
    except Exception:
        pass  # 权限不足忽略，保证程序继续存活


# =====================================================================
# 核心处理逻辑与隔离
# =====================================================================
def parse_search_rules(user_input: str) -> List[List[str]]:
    """解析搜索语法，支持 + 号组合与空格独立匹配"""
    rules = []
    # 兼容中文加号
    raw_rules = user_input.replace('＋', '+').split()
    for raw_rule in raw_rules:
        sub_keywords = [kw.strip().lower() for kw in raw_rule.split('+') if kw.strip()]
        if sub_keywords:
            rules.append(sub_keywords)
    
    # 复杂度越高优先级越高
    return sorted(rules, key=len, reverse=True)


def process_pdf_page(pdf_path: str, page_num: int, rules: List[List[str]]) -> Tuple[str, int, List[str], str]:
    """
    独立页级处理单元：带严格错误捕获的沙盒函数
    返回: (文件路径, 页码, 匹配结果列表, 错误信息)
    """
    global ocr_engine
    import fitz 
    
    results = []
    try:
        # 文件级/页级容错：尝试打开并渲染页面
        with fitz.open(pdf_path) as doc:
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csGRAY)
            img_bytes = pix.tobytes("png")
    except Exception as e:
        return pdf_path, page_num, [], f"PDF解析/渲染失败: {str(e)}"

    try:
        # AI 识别容错：捕获不可预见的模型推理异常
        ocr_result, _ = ocr_engine(img_bytes)
        
        if ocr_result:
            for item in ocr_result:
                line = item[1].strip()
                if not line:
                    continue
                
                line_nospace = line.replace(" ", "").lower()
                for rule in rules:
                    if all(kw in line_nospace for kw in rule):
                        rule_str = " + ".join(rule)
                        info_card = (
                            "--------------------------------------------------\n"
                            f"📄 【来源】 第 {page_num+1} 页\n"
                            f"🎯 【命中规则】 {rule_str}\n"
                            f"📝 【条款原文】\n"
                            f"{line}\n"
                            "--------------------------------------------------"
                        )
                        results.append(info_card)
                        break # 单行命中最高优先级规则即可跳出

        return pdf_path, page_num, results, ""
    
    except Exception as e:
        return pdf_path, page_num, [], f"OCR识别异常: {str(e)}"


def draw_progress_bar(current: int, total: int, bar_length: int = 40):
    """绘制固定原地的动态进度条"""
    if total == 0:
        return
    percent = float(current) * 100 / total
    filled = int(bar_length * current // total)
    bar = '█' * filled + '░' * (bar_length - filled)
    sys.stdout.write(f'\r  [分析进度] {bar} {percent:.1f}% ({current}/{total} 页)')
    sys.stdout.flush()


# =====================================================================
# 主调度与交互层
# =====================================================================
def main():
    print("="*60)
    print(" 自动化 PDF 智能提取工具 (生产环境高可用版)  --由 vv 维护")
    print("="*60)
    print("\n【语法说明】")
    print("  • 用 [空格] 分隔不同的关键字 -> 代表分别独立搜索")
    print("  • 用 [+] 组合不同的关键字 -> 代表必须在同一行同时出现")
    print("  • 示例输入: 收款 支付+%\n")

    # 1. 规则防呆输入
    while True:
        user_input = input("👉 请输入提取规则：\n> ").strip()
        if not user_input:
            print("  [提示] 规则不能为空，请重新输入。")
            continue
            
        rules = parse_search_rules(user_input)
        if not rules:
            print("  [提示] 解析不到有效规则，请重新输入。")
            continue
        break
        
    print(f"\n[设定] 当前生效的检索规则 (共 {len(rules)} 组):")
    for idx, r in enumerate(rules):
        print(f"  规则 {idx+1}: 必须同时包含 {r}")

    # 2. 文件环境检查
    target_folder = os.getcwd()
    pdf_files = [f for f in os.listdir(target_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("\n[中断] 当前目录下未发现任何 PDF 文件。")
        input("按回车键退出程序...")
        return sys.exit(0)

    print(f"\n[系统] 发现 {len(pdf_files)} 个 PDF 文件，正在预读取扫描总页数...")
    
    import fitz
    all_tasks = []
    total_pages = 0
    error_logs = []  # 用于记录无法读取的文件等错误

    # 预扫描防错：跳过损坏的 PDF
    for filename in pdf_files:
        pdf_path = os.path.join(target_folder, filename)
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    error_logs.append(f"[{filename}] 文件被加密，已跳过。")
                    continue
                pages_count = len(doc)
                total_pages += pages_count
                for i in range(pages_count):
                    all_tasks.append((pdf_path, i))
        except Exception as e:
            error_logs.append(f"[{filename}] 无法打开或文件损坏: {e}")

    if total_pages == 0:
        print("\n[中断] 有效处理页数为 0（可能文件均损坏或为空）。")
        for err in error_logs:
            print(f"  - {err}")
        input("按回车键退出程序...")
        return sys.exit(1)

    # 3. 线程防呆配置与硬限制 (防止过度挤占系统资源)
    total_threads = multiprocessing.cpu_count()
    # 核心修改：计算出最大允许的进程数（逻辑线程数的一半，至少为 1）
    max_allowed_workers = max(1, total_threads // 2) 
    
    print(f"\n[系统] 性能检测完成：本机共有 {total_threads} 个逻辑处理器 (线程)。")
    print(f"[系统] 为保证您的电脑不卡顿并发挥最高 AI 运算效率，最大并发数已被硬性锁定为 {max_allowed_workers}。")
    
    while True:
        # 修改提示语，把上限变成 max_allowed_workers
        user_input_cores = input(f"👉 请输入想调用的并发进程数 (范围 1~{max_allowed_workers}，直接按回车默认使用 {max_allowed_workers}): \n> ").strip()
        
        if not user_input_cores:
            max_workers = max_allowed_workers
            print(f"  [设定] 已采用最优推荐配置：{max_workers} 个进程。")
            break
            
        try:
            max_workers = int(user_input_cores)
            if max_workers < 1:
                print("  [错误] 进程数至少为 1，请重新输入。")
            elif max_workers > max_allowed_workers:
                # 核心修改：触发硬拦截，不允许超过一半
                print(f"  [拦截] 为防止电脑卡死，进程数不可超过 {max_allowed_workers}。已自动为您调整为 {max_allowed_workers}。")
                max_workers = max_allowed_workers
                break
            else:
                break
        except ValueError:
            print("  [错误] 只能输入纯数字，请不要输入字母或符号！")

    # 创建输出目录
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir_name = f"提取结果_{timestamp}"
    output_dir = os.path.join(target_folder, output_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[系统] 引擎点火！已分配 {max_workers} 个独立核心，共需扫单 {total_pages} 页。")
    print("[系统] 各进程正在独立初始化 AI 模型，任务执行中...\n")
    
    aggregated_results: Dict[str, Dict[int, List[str]]] = defaultdict(lambda: defaultdict(list))
    completed_pages = 0
    draw_progress_bar(completed_pages, total_pages)

    # 4. 并发执行与监控
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker) as executor:
        futures = {executor.submit(process_pdf_page, task[0], task[1], rules): task for task in all_tasks}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                pdf_path, page_num, results, err_msg = future.result()
                if err_msg:
                    filename = os.path.basename(pdf_path)
                    error_logs.append(f"[{filename} - 第 {page_num+1} 页] {err_msg}")
                elif results:
                    aggregated_results[pdf_path][page_num] = results
            except Exception as exc:
                error_logs.append(f"[严重异常] 进程执行崩溃: {exc}")
            finally:
                completed_pages += 1
                draw_progress_bar(completed_pages, total_pages)

    # 5. 安全写入导出
    print("\n\n[系统] 提取完成，正在生成结构化报告...")
    success_count = 0
    
    for filename in pdf_files:
        pdf_path = os.path.join(target_folder, filename)
        # 如果这个文件压根没进入任务池(损坏/加密)，直接跳过写入
        if not any(task[0] == pdf_path for task in all_tasks):
            continue
            
        file_data = aggregated_results.get(pdf_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_txt_path = os.path.join(output_dir, f"{name_without_ext}_提取结果.txt")
        
        try:
            with open(output_txt_path, "w", encoding="utf-8") as f:
                if file_data:
                    # 按页码顺序写入
                    for p_idx in sorted(file_data.keys()):
                        f.write("\n\n".join(file_data[p_idx]) + "\n\n")
                    success_count += 1
                else:
                    f.write("未发现匹配当前规则的内容。\n")
        except Exception as e:
            error_logs.append(f"[{filename}] 写入结果文件失败: {e}")

    # 6. 运行报告总结
    print("\n" + "="*60)
    print(f"🎉 任务结束！")
    print(f"✅ 成功提取: 在 {success_count} 个文件中发现了匹配项。")
    print(f"📂 存放目录: {output_dir_name}")
    
    if error_logs:
        print("\n⚠️ 运行期间产生以下警告/错误 (已自动绕过):")
        for err in error_logs[:10]:  # 最多展示前 10 条避免刷屏
            print(f"  - {err}")
        if len(error_logs) > 10:
            print(f"  ... 等共 {len(error_logs)} 条异常。")
            
    print("="*60)
    input("按回车键退出程序...")


if __name__ == "__main__":
    # Windows 平台打包 exe 必须带上这一句
    multiprocessing.freeze_support()
    # 全局异常兜底，防止直接闪退黑屏
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[中断] 用户强制结束了程序。")
    except Exception as e:
        print(f"\n\n[崩溃] 发生未预期的致命错误:\n{e}")
        input("按回车键退出...")