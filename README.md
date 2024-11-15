# Video_Preview_Tool

## Overview
The `Video_Preview_Tool` is a Python application designed to provide users with a simple and efficient way to preview and manage video files. This tool supports various video formats and offers features such as frame extraction, video trimming, and more.

## Features
- **Video Playback**: Supports playback of various video formats.
- **Frame Extraction**: Extract frames from video files at specified intervals.
- **Video Trimming**: Trim video files to desired lengths.
- **User-Friendly Interface**: Simple and intuitive interface for ease of use.
- **Quick Data Annotation**: Easily annotate data through input fields, such as whether to use the video, presence of black borders, presence of subtitles, and video intro trim duration.
- **Metadata Management**: Quickly establish and manage video metadata information.

## Installation
To install the `Video_Preview_Tool`, follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/weizart/Video_Preview_Tool.git
   ```
2. Navigate to the project directory:
   ```sh
   cd Video_Preview_Tool
   ```
3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Start the application:
   ```sh
   streamlit run app.py
   ```

## Usage
Here are the basic steps to use the `Video_Preview_Tool`:

1. Open the application by running the command streamlit run app.py.
2. Load a video file by selecting it from the directory list.
3. Change VIDEOPATH and TEMPPATH as per your requirements in the configuration.
4. Use the playback controls to preview the video.
5. To extract frames, specify the interval and use the provided options.
6. To trim the video, set the start and end points using the interface.
7. Optionally, change the beginning and ending times to clip the video.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
This repo belonging to @hpcaitech

Main Contributor: Thanks to @ouyangchushang
