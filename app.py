
# streamlit run app.py

import os
import streamlit as st
import pandas as pd
import ast 
from concurrent.futures import ThreadPoolExecutor
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# 基础目录，修改为自己的任务路径
BASE_DIR = "/mnt/jfs2/hdd2/sora/data/videos/purchase/movie_baidudisk/data/3-1080p-20241108/task_3/_series"
# 临时目录，用于保存截取的视频，修改为自己的一个文件夹
TEMP_DIR = "/home/weiziang/tmp/1116"
os.makedirs(TEMP_DIR, exist_ok=True)

# CSV 文件路径
CSV_FILENAME = "meta.csv"
csv_path = os.path.join(TEMP_DIR, CSV_FILENAME)

# 获取基础目录中的所有子文件夹，并按文件夹名排序
def get_video_directories(base_dir):
    directories = []
    for folder in os.listdir(base_dir):  # 仅包含目录
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            directories.append({"Name": folder, "Absolute Path": folder_path})
    # 对 directories 列表按名称排序
    directories = sorted(directories, key=lambda x: x["Name"])
    return directories

video_data = get_video_directories(BASE_DIR)
directory_names = [dir["Name"] for dir in video_data]
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# 获取指定目录中的所有文件（仅视频文件），并按文件名排序
def get_all_files(path):
    if os.path.isdir(path):
        return sorted([os.path.join(path, file) for file in os.listdir(path) if file.lower().endswith((".mp4", ".mkv", ".avi"))])  # 仅视频文件
    return []

# 截取视频部分
def trim_video(video_path):
    # 获取文件夹名和文件名
    folder_name = os.path.basename(os.path.dirname(video_path))
    file_name = os.path.basename(video_path)
    trimmed_file_name = f"{folder_name}_{file_name}"
    trimmed_path = os.path.join(TEMP_DIR, trimmed_file_name)
    if not os.path.exists(trimmed_path):
        try:
            ffmpeg_extract_subclip(video_path, 0, 10, targetname=trimmed_path)
        except Exception as e:
            st.error(f"截取视频时出错: {e}")
            return None
    return trimmed_path

# 后台批量裁切所有视频
@st.cache_data(show_spinner=True)
def batch_trim_videos(video_files):
    video_files = [vf for vf in video_files if vf is not None]
    trimmed_videos = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(trim_video, video_files)
        for result in results:
            if result:
                trimmed_videos.append(result)
    return trimmed_videos

# 获取视频文件的大小和时长
def get_file_metadata(file_path):
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)

    # 视频总时长（仅限视频格式）
    duration = None
    if file_path.lower().endswith((".mp4", ".mkv", ".avi")):  # 检查是否为视频文件，如果有特殊格式加在这里
        try:
            with VideoFileClip(file_path) as clip:
                duration = clip.duration  # 秒
        except Exception as e:
            duration = None  # 如果无法加载视频时长，则返回None

    return file_size_mb, duration

# 获取每个文件夹的代表文件（按文件名排序后的第一个文件）
def get_representative_file(files):
    if files:
        return files[0]
    return None

# 显示当前视频目录中的文件，并添加智能交互功能
def display_files(index, df):
    title = video_data[index]["Name"]
    path = video_data[index]["Absolute Path"]

    # 显示标题
    st.header(f"目录: {title}")

    # 获取并显示文件
    all_files = get_all_files(path)
    if not all_files:
        st.write("该目录中没有找到视频文件。")
    else:
        # 获取代表文件
        representative = get_representative_file(all_files)
        if representative is None:
            st.write("该目录中没有找到代表视频文件。")
            return

        # 从 DataFrame 中获取代表文件的设置
        row = df[df['path'] == representative]
        if not row.empty:
            row = row.iloc[0]
            discard = row.get('discard', '否') == '是'
            subtitle = row.get('human_subtitle', 0)
            border = row.get('human_border', 0)
            watermark = row.get('human_watermark', "[]")
            # 将字符串转换为列表
            try:
                watermark = ast.literal_eval(watermark)
            except:
                watermark = []
            beginning = row.get('human_beginning', '')
            # 分解时间戳为小时、分钟、秒
            try:
                h, m, s = map(int, beginning.split(":"))
            except:
                h, m, s = 0, 0, 0
        else:
            discard = False
            subtitle = 0
            border = 0
            watermark = []
            h, m, s = 0, 0, 0

        file_name = os.path.basename(representative)
        file_size_mb, duration = get_file_metadata(representative)

        st.subheader(f"代表文件名: {file_name}")
        st.write(f"文件大小: {file_size_mb:.2f} MB")
        if duration:
            st.write(f"视频总时长: {int(duration // 60)} 分 {int(duration % 60)} 秒")
        else:
            st.write("非支持的视频格式或视频文件，无法显示时长")
        if representative.lower().endswith((".mp4", ".mkv", ".avi")):
            trimmed_video = trim_video(representative)
            st.video(trimmed_video)

        with st.form(key=f"form_{path}"):
            discard_option = st.radio(
                f"{file_name} - 是否丢弃？",
                options=["否", "是"],
                index=1 if discard else 0,
                key=f"discard_{path}"
            )
            is_discard = (discard_option == "是")

            if not is_discard:
                subtitles_option = st.checkbox("字幕", value=bool(subtitle), key=f"subtitles_{path}")
                black_borders_option = st.checkbox("黑边", value=bool(border), key=f"blackborders_{path}")

                # 修改水印部分：使用五个复选框
                st.markdown("**水印位置**")
                watermark_options = {
                    "左上": "0",
                    "右上": "1",
                    "左下": "2",
                    "右下": "3",
                    "其他位置/浮动/飘动": "4"
                }
                selected_watermarks = []
                for label, value in watermark_options.items():
                    if st.checkbox(label, key=f"watermark_{value}_{path}"):
                        selected_watermarks.append(value)

                # 设置开始时间
                col_h, col_m, col_s = st.columns(3)
                with col_h:
                    hours = st.number_input(
                        "时 (H)",
                        min_value=0,
                        value=h,
                        step=1,
                        key=f"hours_{path}"
                    )
                with col_m:
                    minutes = st.number_input(
                        "分 (M)",
                        min_value=0,
                        max_value=59,
                        value=m,
                        step=1,
                        key=f"minutes_{path}"
                    )
                with col_s:
                    seconds = st.number_input(
                        "秒 (S)",
                        min_value=0,
                        max_value=59,
                        value=s,
                        step=1,
                        key=f"seconds_{path}"
                    )
            else:
                subtitles_option = False
                black_borders_option = False
                selected_watermarks = []
                hours, minutes, seconds = 0, 0, 0

            submitted = st.form_submit_button("保存设置")
            if submitted:
                if not is_discard:
                    beginning_option = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                    # 获取该目录下所有文件
                    for file_path in all_files:
                        df.loc[df['path'] == file_path, 'human_subtitle'] = int(subtitles_option)
                        df.loc[df['path'] == file_path, 'human_border'] = int(black_borders_option)
                        df.loc[df['path'] == file_path, 'human_watermark'] = str(selected_watermarks)  # 存储为字符串
                        df.loc[df['path'] == file_path, 'human_beginning'] = beginning_option
                        df.loc[df['path'] == file_path, 'discard'] = 0
                    st.success(f"设置已保存: {title} 目录下所有文件")
                else:
                    # 获取该目录下所有文件
                    for file_path in all_files:
                        df.loc[df['path'] == file_path, 'human_subtitle'] = 0
                        df.loc[df['path'] == file_path, 'human_border'] = 0
                        df.loc[df['path'] == file_path, 'human_watermark'] = "[]"  # 清空水印
                        df.loc[df['path'] == file_path, 'human_beginning'] = ''
                        df.loc[df['path'] == file_path, 'discard'] = 1
                    st.warning(f"已丢弃: {title} 目录下所有文件")

                # 将 DataFrame 保存到 CSV
                df.to_csv(csv_path, index=False)

# 导航功能
def previous_video():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1  # 减小索引

def next_video():
    if st.session_state.current_index < len(video_data) - 1:
        st.session_state.current_index += 1  # 增大索引

# Streamlit应用结构
st.title("智能视频预览器")

# 检查和初始化 CSV 文件
if os.path.exists(csv_path):
    try:
        df = pd.read_csv(csv_path, converters={'human_watermark': ast.literal_eval})  # 将human_watermark转换为列表
        # 确保 'path' 列存在
        if 'path' not in df.columns:
            st.error("CSV 文件缺少 'path' 列。请确保 CSV 格式正确。")
            st.stop()
        # 确保所有必要的列存在
        for column in ['human_subtitle', 'human_border', 'human_watermark', 'human_beginning', 'discard']:
            if column not in df.columns:
                if column in ['human_subtitle', 'human_border', 'human_watermark']:
                    df[column] = 0 if column != 'human_watermark' else "[]"
                elif column == 'discard':
                    df[column] = '否'
                elif column == 'human_beginning':
                    df[column] = ''
    except Exception as e:
        st.error(f"读取 CSV 文件时出错: {e}")
        st.stop()
else:
    # 创建 CSV 文件，填充 'path' 列
    all_video_paths = []
    for dir in video_data:
        path = dir["Absolute Path"]
        files = get_all_files(path)
        all_video_paths.extend(files)
    # 创建 DataFrame
    df = pd.DataFrame({
        'path': all_video_paths,
        'human_subtitle': 0,
        'human_border': 0,
        'human_watermark': "[]",
        'human_beginning': '',
        'discard': 0
    })
    # 保存到 CSV
    df.to_csv(csv_path, index=False)
    st.success(f"已创建新的 CSV 文件并初始化路径: {csv_path}")

representative = []
for dir in video_data:
    path = dir["Absolute Path"]
    file = get_representative_file(get_all_files(path))
    representative.append(file)
trimmed_videos = batch_trim_videos(representative)
st.success(f"已完成共计 {len(trimmed_videos)}条视频预处理")

# 顶部下拉选框，选择当前视频目录，支持按文件名搜索
selected_directory = st.selectbox("选择视频目录", directory_names, index=st.session_state.current_index)

# 更新当前索引
st.session_state.current_index = directory_names.index(selected_directory)

# 显示当前目录中的文件
display_files(st.session_state.current_index, df)

# 导航按钮
col1, col2 = st.columns(2)
with col1:
    st.button("上一个", on_click=previous_video)

with col2:
    st.button("下一个", on_click=next_video)

# 隐藏 DataFrame 信息（仅用于调试，可删除）
# st.write(df)
