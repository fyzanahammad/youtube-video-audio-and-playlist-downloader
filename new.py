import streamlit as st
import yt_dlp
import os
from typing import Optional, Tuple, List
from datetime import datetime

# Initialize session state
if 'url_list' not in st.session_state:
    st.session_state.url_list = [""]

def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"

def get_video_info(url: str) -> Tuple[Optional[str], Optional[str], bool]:
    """Get video title and thumbnail URL"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title'), info.get('thumbnail'), True
    except Exception as e:
        return None, None, False

def download_video(url: str, audio_only: bool = False) -> Optional[Tuple[str, bytes]]:
    """Download video and return filename and data"""
    try:
        temp_dir = "temp_downloads"
        os.makedirs(temp_dir, exist_ok=True)
        
        output_template = os.path.join(temp_dir, f'%(title)s.%(ext)s')
        
        if audio_only:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            }
        else:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if audio_only:
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            # Read the file data
            with open(filename, 'rb') as f:
                file_data = f.read()
            
            # Clean up temp file
            try:
                os.remove(filename)
            except:
                pass
            
            return os.path.basename(filename), file_data

    except Exception as e:
        st.error(f"Download failed: {str(e)}")
        return None

def get_binary_file_downloader_html(bin_data, file_label='File', file_name='file.txt'):
    """Generate HTML code for downloading binary data"""
    import base64
    b64 = base64.b64encode(bin_data).decode()
    download_link = f'''
        <a href="data:application/octet-stream;base64,{b64}" 
           download="{file_name}" 
           style="text-decoration:none;padding:8px 15px;background-color:#4CAF50;color:white;border-radius:5px;cursor:pointer;">
            📥 Save {file_label}
        </a>
    '''
    return download_link

def main():
    st.title("🎥 YouTube Downloader")
    st.markdown("Download your favorite YouTube videos!")

    option = st.radio("What would you like to download?", 
                     ["🎵 Audio Only", "🎬 Video with Audio"],
                     horizontal=True)
    
    audio_only = option == "🎵 Audio Only"
    
    # URL input section
    for i, url in enumerate(st.session_state.url_list):
        col1, col2 = st.columns([6, 1])
        with col1:
            new_url = st.text_input(
                "Enter YouTube URL:",
                value=url,
                key=f"url_{i}",
                placeholder="https://www.youtube.com/watch?v=..."
            )
            st.session_state.url_list[i] = new_url
        
        with col2:
            if len(st.session_state.url_list) > 1:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.url_list.pop(i)
                    st.rerun()
    
    if st.button("➕ Add Another URL"):
        st.session_state.url_list.append("")
        st.rerun()
    
    # Preview and download section
    urls_to_process = [url for url in st.session_state.url_list if url.strip()]
    
    if urls_to_process:
        st.subheader("Videos to Download")
        for url in urls_to_process:
            title, thumbnail_url, is_valid = get_video_info(url)
            if is_valid:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if thumbnail_url:
                        st.image(thumbnail_url, width=120)
                with col2:
                    st.markdown(f"**{title}**")
                with col3:
                    if st.button("⬇️ Download", key=f"download_{url}"):
                        with st.spinner("Downloading..."):
                            result = download_video(url, audio_only)
                            if result:
                                filename, file_data = result
                                st.markdown(
                                    get_binary_file_downloader_html(
                                        file_data,
                                        'File',
                                        filename
                                    ),
                                    unsafe_allow_html=True
                                )
                                st.success("✅ Download complete!")
                st.markdown("---")

if __name__ == "__main__":
    main()
