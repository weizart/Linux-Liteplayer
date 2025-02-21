import ast
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from moviepy.video.io.VideoFileClip import VideoFileClip

# =========
# Utils
# =========
def create_and_set_group(dir_path, group_name="share"):
    try:
        if not os.path.exists(dir_path):
            # 创建目录（如果不存在）
            os.makedirs(dir_path, exist_ok=True)

            # 设置组权限
            subprocess.run(["chgrp", group_name, dir_path], check=True)

            # 确保目录的权限允许组访问
            subprocess.run(["chmod", "g+rwx", dir_path], check=True)

    except Exception as e:
        print(f"An error occurred: {e}")


# 获取目录中的视频文件
def get_video_files(path):
    if os.path.isdir(path):
        return sorted(
            [
                os.path.join(path, file)
                for file in os.listdir(path)
                if file.lower().endswith((".mp4", ".mkv", ".avi", ".rmvb", ".flv", ".mov", "wmv"))  # 仅视频文件
            ]
        )
    return []


# 获取所有子目录
def get_video_directories(base_dir):
    directories = [
        {"Name": folder, "Absolute Path": os.path.join(base_dir, folder)}
        for folder in sorted(os.listdir(base_dir))
        if os.path.isdir(os.path.join(base_dir, folder))
    ]
    directories = sorted(directories, key=lambda x: x["Name"])
    return directories


# 获取任务列表
def get_task_list(txt_path):
    with open(txt_path, "r") as f:
        return f.read().splitlines()


# =========
# Task
# =========

DEFAULT_VALUES = {
    "human_subtitle": 0,
    "human_border": 0,
    "human_watermark": "[]",
    "human_timestamp": "('-1','-1')",
    "human_category": None,
    "raw_resolution": 0,
    "raw_fps": None,
    "id": None,
    "discard": 0,
    "new_name": None,
    "used_time": 0,
}


def validate_and_fill_columns(df, default_values):
    """
    验证 DataFrame 中的列是否存在，不存在则填充默认值。
    """
    for column, default_value in default_values.items():
        if column not in df.columns:
            df[column] = default_value
    return df


def initialize_csv(csv_path, video_data):
    """
    初始化 CSV 文件，如果不存在则创建新的文件。
    """
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, converters={"human_watermark": lambda x: list(map(int, ast.literal_eval(x)))})  # 将 human_watermark 转换为列表
            if "path" not in df.columns:
                st.error("CSV 文件缺少 'path' 列。请确保 CSV 格式正确。")
                st.stop()
            df = validate_and_fill_columns(df, DEFAULT_VALUES)
            st.success(f"已加载任务（含有{len(df)}个视频）: {csv_path}")
        except Exception as e:
            st.error(f"读取 CSV 文件时出错: {e}")
            st.stop()
    else:
        # 创建新的 DataFrame 并填充路径列
        all_video_paths = [file for dir in video_data for file in get_video_files(dir["Absolute Path"])]
        df = pd.DataFrame({"path": all_video_paths, **DEFAULT_VALUES})
        # 保存到 CSV 文件
        df.to_csv(csv_path, index=False)
        st.success(f"已创建新的 CSV 文件并初始化路径: {csv_path}")
    return df


def get_task_info(task_dir: str):
    csv_path = os.path.join(task_dir, "meta.csv")
    df = initialize_csv(csv_path, get_video_directories(task_dir))
    video_data = get_video_directories(task_dir)
    directory_names = [dir["Name"] for dir in video_data]

    return csv_path, video_data, directory_names, df


def get_vid_name(vid_data, df):
    vid_dir = df["path"].apply(os.path.dirname)
    target = vid_data["Absolute Path"]
    if not df[vid_dir == target].empty:
        row = df[vid_dir == target].iloc[0]
        if not pd.isna(row["new_name"]):
            return row["new_name"]
    else:
        st.error("找不到视频文件的相关信息。")
    return vid_data["Name"]


# =========
# Videos
# =========


# 判断视频是否已经处理好
def is_video_processed(video_path, suffix):
    folder_name = os.path.basename(os.path.dirname(video_path))
    file_name = os.path.basename(video_path)
    # 如果是 .rmvb 文件，检查 .mp4 格式的文件是否处理过
    if file_name.lower().endswith(".rmvb"):
        trimmed_file_name = f"{folder_name}_{file_name.split('.')[0]}_{suffix}.mp4"
    else:
        trimmed_file_name = f"{folder_name}_{file_name.split('.')[0]}_{suffix}.{file_name.split('.')[-1]}"
    trimmed_path = os.path.join(TEMP_DIR, trimmed_file_name)

    return os.path.exists(trimmed_path)


def trim_video(video_path, start_time, duration, suffix):
    folder_name = os.path.basename(os.path.dirname(video_path))
    file_name = os.path.basename(video_path)
    # 如果是 .rmvb 文件，检查 .mp4 格式的文件是否处理过
    if file_name.lower().endswith(".rmvb"):
        trimmed_file_name = f"{folder_name}_{file_name.split('.')[0]}_{suffix}.mp4"
    else:
        trimmed_file_name = f"{folder_name}_{file_name.split('.')[0]}_{suffix}.{file_name.split('.')[-1]}"
    trimmed_path = os.path.join(TEMP_DIR, trimmed_file_name)

    if os.path.exists(trimmed_path):
        return trimmed_path

    try:
        ffmpeg_command = [
            "ffmpeg",
            "-i", video_path,
            "-ss", start_time,
            "-t", duration,
            "-map", "0:v",
            "-c:v", "libx264",
            "-vf", "scale=854:480,fps=24",
            "-sn", "-an",
            "-y",
            "-fflags", "+genpts",
            "-ignore_unknown",
            trimmed_path,
        ]

        subprocess.run(ffmpeg_command, check=True)

    except Exception as e:
        st.error(f"截取视频时发生错误: {e}")
        return None

    return trimmed_path


# 获取视频元数据
def get_file_metadata(file_path):
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    duration, fps, resolution = None, None, None

    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", 
            "stream=r_frame_rate,height,width",
            "-show_entries", 
            "format=duration",
            "-of", "json", 
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        metadata = eval(result.stdout)

        # 解析数据
        duration = float(metadata["format"]["duration"])
        fps = eval(metadata["streams"][0]["r_frame_rate"])
        width = int(metadata["streams"][0]["width"])
        height = int(metadata["streams"][0]["height"])
        resolution = min(width, height)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

    return file_size_mb, duration, fps, resolution


# 选取代表文件
def get_representation(index, video_data):
    path = video_data[index]["Absolute Path"]
    video_files = get_video_files(path)

    if not video_files:
        st.error("该目录中没有找到视频文件。")
        return None

    representative = video_files[1] if len(video_files) > 1 else video_files[0]
    return representative


# 判断预先加载是否完成
def is_buffered(index, video_data):
    representative = get_representation(index, video_data)
    if representative is None:
        return False
    return is_video_processed(representative, "head") and is_video_processed(representative, "tail")


# 预先加载视频
def buffer_video(index, video_data):
    representative = get_representation(index, video_data)
    if representative is None:
        return

    _, duration, _, _ = get_file_metadata(representative)
    trim_video(representative, "00:00:00", "00:05:00", "head")
    trim_video(representative, f"{duration - 600}", "00:05:30", "tail") if duration else None


# 显示目录中的文件和相关设置
def display_files(index, video_data, df, csv_path):
    path = video_data[index]["Absolute Path"]
    video_files = get_video_files(path)
    representative = get_representation(index, video_data)

    if representative is None:
        st.error("无法加载视频，因为该目录中没有视频文件。")
        return

    row = df[df["path"] == representative].iloc[0] if not df[df["path"] == representative].empty else {}
    file_name = os.path.basename(representative)
    file_size_mb, duration, fps, resolution = get_file_metadata(representative)

    duration_str = f"{int(duration // 60)} 分 {int(duration % 60)} 秒" if duration else "无法获取视频时长"
    st.markdown(f"* 代表视频: {file_name}\n* 文件大小: {file_size_mb:.2f} MB\n* 时长: {duration_str}")

    trimmed_video_head = trim_video(representative, "00:00:00", "00:05:00", "head")
    trimmed_video_tail = trim_video(representative, f"{duration - 600}", "00:07:00", "tail") if duration else None

    st.subheader("片头视频")
    st.video(trimmed_video_head)
    st.subheader("片尾视频")
    st.video(trimmed_video_tail)

    # form
    start_h, start_m, start_s = 0, 0, 0
    end_h, end_m, end_s = 0, 0, 0
    newname, subtitle, border, category, selected_watermarks = None, False, False, None, []

    with st.form(key=f"form_{path}"):
        discard = st.radio("**是否丢弃**", ["否", "是"], index=int(row.get("discard", 0)), key=f"discard_{path}")

        if discard == "否":
            newname = st.text_input("**新文件名（豆瓣）**", value=get_vid_name(video_data[index], df), key=f"newname_{path}")
            subtitle = st.checkbox("**有字幕**", value=row.get("human_subtitle", False), key=f"subtitles_{path}")
            border = st.checkbox("**有黑边**", value=row.get("human_border", False), key=f"blackborders_{path}")
            category = st.selectbox(
                "**分类**",
                options=[0, 1, 2, 3, 4],
                index=0,
                key=f"human_category_{path}",
                format_func=lambda x: ["0 电影", "1 电视剧", "2 纪录片", "3 综艺", "4 动漫"][x],
            )
            st.markdown("**水印位置**（没有则不选）")
            watermark_options = {"左上": 0, "右上": 1, "左下": 2, "右下": 3, "其他": 4}
            selected_watermarks = []
            for col, (label, value) in zip(st.columns(len(watermark_options)), watermark_options.items()):
                with col:
                    w_ck = st.checkbox(label, key=f"watermark_{value}_{path}")
                    if w_ck:
                        selected_watermarks.append(value)

            # 片头标注
            st.markdown("**片头时间**")
            col_start_h, col_start_m, col_start_s = st.columns(3)
            with col_start_h:
                start_h = st.number_input("时 (H)", min_value=0, value=start_h, step=1, key=f"start_hours_{path}")
            with col_start_m:
                start_m = st.number_input(
                    "分 (M)", min_value=0, max_value=59, value=start_m, step=1, key=f"start_minutes_{path}"
                )
            with col_start_s:
                start_s = st.number_input(
                    "秒 (S)", min_value=0, max_value=59, value=start_s, step=1, key=f"start_seconds_{path}"
                )

            # 片尾标注
            st.markdown("**片尾时间**")
            st.subheader("脚本在标注片尾时间时会自动加上之前的时间，不需要人工计算!!!")
            col_end_h, col_end_m, col_end_s = st.columns(3)
            with col_end_h:
                end_h = st.number_input("时 (H)", min_value=0, value=end_h, step=1, key=f"end_hours_{path}") + int(
                    (duration - 600) / 3600
                )
            with col_end_m:
                end_m = st.number_input(
                    "分 (M)", min_value=0, max_value=59, value=end_m, step=1, key=f"end_minutes_{path}"
                ) + int((duration - 600) / 60)
            with col_end_s:
                end_s = st.number_input(
                    "秒 (S)", min_value=0, max_value=59, value=end_s, step=1, key=f"end_seconds_{path}"
                ) + int((duration - 600) % 60)

        if st.form_submit_button("保存"):
            if end_s > 60:
                end_s %= 60
                end_m += 1
            if end_m > 60:
                end_m %= 60
                end_h += 1

            timestamp = f"('{int(start_h):02d}:{int(start_m):02d}:{int(start_s):02d}','{int(end_h):02d}:{int(end_m):02d}:{int(end_s):02d}')"
            current_time = datetime.now()
            elapsed_time = current_time - st.session_state["start_time"]
            for file_path in video_files:
                df.loc[
                    df["path"] == file_path,
                    [
                        "human_subtitle",
                        "human_border",
                        "human_watermark",
                        "human_timestamp",
                        "human_category",
                        "discard",
                        "new_name",
                        "used_time",
                    ],
                ] = [
                    int(subtitle),
                    int(border),
                    str(selected_watermarks),
                    timestamp,
                    int(category) if category is not None else None,
                    1 if discard == "是" else 0,
                    newname,
                    elapsed_time.seconds,
                ]
                df.loc[df["path"] == file_path, ["id", "raw_fps", "raw_resolution"]] = [None, int(fps), int(resolution)]
            df.to_csv(csv_path, index=False)
            st.success("设置已保存")
            st.info(f"标注该视频耗时: {elapsed_time.seconds} 秒")


# 导航按钮
scroll_script = """
<script>
    function scrollToTop() {
        window.scrollTo(0, 0);
    }
</script>
"""


def scroll_to(element_id):
    components.html(
        f"""
        <script>
            var element = window.parent.document.getElementById("{element_id}");
            element.scrollIntoView();
        </script>
    """.encode()
    )


def previous_video():
    if st.session_state.current_vid_index > 0:
        st.session_state.current_vid_index -= 1
        st.session_state.start_time = datetime.now()
        scroll_to("select_video")
        st.rerun()
    else:
        st.warning("已经是第一个视频了")


def next_video(total):
    if st.session_state.current_vid_index < total - 1:
        st.session_state.current_vid_index += 1
        st.session_state.start_time = datetime.now()
        scroll_to("select_video")
        st.rerun()
    else:
        st.warning("已经是最后一个视频了")


TASK_LIST_PATH = os.environ.get("${TXT_PATH}", "temptask.txt")
TASK_LIST = get_task_list(TASK_LIST_PATH)
TEMP_DIR = os.environ.get("TEMP_DIR", "${DEFAULT_TEMPPATH}")
create_and_set_group(TEMP_DIR, group_name="share")

if "current_task_index" not in st.session_state:
    st.session_state.current_task_index = 0
    st.session_state.current_vid_index = 0
    st.session_state.refresh_count = 0
    st.session_state.buffering_task = None
    st.session_state.buffering_index = None
if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.now()


def main():
    # 初始化
    st.set_page_config(
        page_title="Linux Liteplayer",
        page_icon="📘",
    )
    st.title("Linux Liteplayer")

    # 选择任务
    old_task = st.session_state.current_task_index
    st.subheader("选择任务", anchor="select_task")
    selected_task = st.selectbox(
        "选择任务", TASK_LIST, index=st.session_state.current_task_index, label_visibility="hidden"
    )
    st.session_state.current_task_index = TASK_LIST.index(selected_task)
    csv_path, video_data, directory_names, df = get_task_info(selected_task)
    if old_task != st.session_state.current_task_index:
        st.session_state.current_vid_index = 0
        st.session_state.start_time = datetime.now()

    # 选择目录
    st.subheader("选择视频", anchor="select_video")
    selected_directory = st.selectbox(
        "选择视频",
        directory_names,
        index=st.session_state.current_vid_index,
        label_visibility="hidden",
        key="video_select",
    )
    st.session_state.current_vid_index = directory_names.index(selected_directory)
    st.progress((st.session_state.current_vid_index + 1) / len(video_data))
    vid_name = get_vid_name(video_data[st.session_state.current_vid_index], df)
    st.success(f"第{st.session_state.current_vid_index + 1}个视频：{vid_name}")

    # 显示视频文件和表单
    display_files(st.session_state.current_vid_index, video_data, df, csv_path)

    # 预先处理下一个视频
    if st.session_state.current_vid_index < len(video_data) - 1:
        next_index = st.session_state.current_vid_index + 1
        buffered = is_buffered(next_index, video_data)
        if buffered:
            st.success("下一个视频已预先加载")
        elif st.session_state.buffering_task == selected_task and st.session_state.buffering_index == next_index:
            st.warning("正在预先加载下一个视频，请稍等后点击刷新按钮")
        else:
            st.warning("已启动预先加载下一个视频，请稍等后点击刷新按钮")
            st.session_state.buffering_task = selected_task
            st.session_state.buffering_index = next_index
            with ThreadPoolExecutor() as executor:
                executor.submit(buffer_video, next_index, video_data)

    # 导航按钮
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("上一个"):
            previous_video()
    with col2:
        if st.button("下一个"):
            next_video(len(video_data))
    with col3:
        if st.button("刷新"):
            st.session_state.refresh_count += 1
            st.rerun()
        st.success(f"已刷新页面 {st.session_state.refresh_count} 次")

main()
