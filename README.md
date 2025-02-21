# Linux-Lite Player

## Motivation
Are you experiencing these challenges?
- Slow loading times when accessing videos on remote servers
- Remote annotation teams struggling to access server-stored videos
- Need for efficient video annotation capabilities across distributed teams

Linux-Lite Player solves these problems by providing a web-based solution deployed on your server, allowing you to watch server-hosted videos through your local browser via remote port access. It includes an integrated annotation window for efficient video data labeling and collection.

## Features
- **Lightweight Web Interface**: Access server videos through any modern web browser
- **Remote Access Optimization**: Efficiently stream videos from server to local browser
- **Integrated Annotation Tools**: 
  - Quick data annotation interface
  - Video metadata management
  - Frame-by-frame navigation
  - Customizable annotation fields
- **Video Processing Capabilities**:
  - Frame extraction at specified intervals
  - Video trimming and clipping
  - Support for various video formats
  - Black border detection
  - Subtitle presence checking
  - Intro trimming functionality

## Installation

1. Clone the repository:
```sh
git clone https://github.com/weizart/Video_Preview_Tool.git
```

2. Navigate to project directory:
```sh
cd Video_Preview_Tool
```

3. Install dependencies:
```sh
pip install -r requirements.txt
```

4. Configure paths:
Edit `config.py` to set your video and temporary directories:
```python
VIDEOPATH = "/path/to/your/videos"
TEMPPATH = "/path/to/temp/directory"
```

5. Start the server:
```sh
streamlit run app.py
```

## Usage

1. After starting the server, access the web interface through your browser using the provided port
2. Navigate the directory list to select videos
3. Use the video player controls for playback
4. Access annotation tools through the sidebar
5. Save annotations and metadata directly through the interface

## Deployment Tips
- Configure your server's firewall to allow access through the designated port
- For team usage, consider setting up user authentication
- Regularly backup annotation data
- Monitor server resources when multiple users are accessing videos

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
