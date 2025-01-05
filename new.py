import streamlit as st
import yt_dlp
import os
from typing import Optional, Tuple, List
from datetime import datetime
import io

# Initialize session state
if 'url_list' not in st.session_state:
    st.session_state.url_list = [""]
if 'format_selections' not in st.session_state:
    st.session_state.format_selections = {}

def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"

def format_speed(bytes_per_second):
    """Format speed to human readable format"""
    return f"{format_size(bytes_per_second)}/s"

def get_video_formats(url: str) -> List[dict]:
    """Get available formats for a video with size information"""
    try:        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            valid_formats = []
            
            # Get combined formats (video+audio)
            for f in info['formats']:
                if f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none':
                    height = f.get('height')
                    format_note = f.get('format_note', '')
                    
                    # Skip formats without height or resolution info
                    if height is None and not format_note:
                        continue
                    
                    # Handle filesize - use filesize or filesize_approx, default to 0 if both are None
                    filesize = f.get('filesize') or f.get('filesize_approx') or 0
                    size_mb = filesize / (1024 * 1024) if filesize else 0
                    
                    # Use format_note for resolution if height is not available
                    resolution = f'{height}p' if height is not None else format_note
                    
                    format_info = {
                        'format_id': f['format_id'],
                        'ext': f.get('ext', 'mp4'),
                        'resolution': resolution,
                        'filesize': size_mb,
                        'format_note': format_note,
                        'height': height if height is not None else 0
                    }
                    valid_formats.append(format_info)
            
            # Sort by height, handling None values safely
            valid_formats.sort(key=lambda x: x['height'] or 0)
            
            if not valid_formats:
                # If no combined formats found, add best available format
                best_format = None
                for f in info['formats']:
                    if f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none':
                        best_format = f
                        break
                
                if best_format:
                    filesize = best_format.get('filesize') or best_format.get('filesize_approx') or 0
                    size_mb = filesize / (1024 * 1024) if filesize else 0
                    valid_formats.append({
                        'format_id': best_format['format_id'],
                        'ext': best_format.get('ext', 'mp4'),
                        'resolution': 'Best Quality',
                        'filesize': size_mb,
                        'format_note': best_format.get('format_note', 'Best Quality'),
                        'height': 0
                    })
            
            return valid_formats
            
    except Exception as e:
        st.error(f"Error getting formats: {str(e)}")
        import traceback
        st.write("DEBUG: Full error traceback:")
        st.code(traceback.format_exc())
        return []

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

def download_video(url: str, audio_only: bool = False, format_id: Optional[str] = None) -> Tuple[bool, str, bytes]:
    """Download a video and return success status, filename, and file content"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best' if audio_only else format_id or 'best',
            'outtmpl': '%(title)s.%(ext)s'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            
            # Create a BytesIO object to store the file content
            file_content = io.BytesIO()
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        progress = (downloaded / total)
                        st.session_state[f'progress_{url}'] = progress

            ydl_opts['progress_hooks'] = [progress_hook]
            
            # Download to memory
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
                # Read the downloaded file into memory
                with open(filename, 'rb') as f:
                    file_content.write(f.read())
                
                # Delete the local file
                os.remove(filename)
            
            return True, filename, file_content.getvalue()
            
    except Exception as e:
        st.error(f"Error downloading video: {str(e)}")
        return False, "", b""

def get_binary_file_downloader_html(bin_data, file_label='File', file_name='file.txt'):
    """Generate HTML code for downloading binary data"""
    import base64
    b64 = base64.b64encode(bin_data).decode()
    custom_css = '''
        <style>
            .download-link {
                text-decoration: none;
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            .download-link:hover {
                background-color: #45a049;
            }
        </style>
    '''
    download_link = f'''
        {custom_css}
        <a href="data:application/octet-stream;base64,{b64}" 
           download="{file_name}" 
           class="download-link">
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
            
            # Show format selector for videos
            if new_url and not audio_only:
                formats = get_video_formats(new_url)
                if formats:
                    format_options = []
                    for f in formats:
                        size_text = f"({f['filesize']:.1f}MB)" if f['filesize'] > 0 else ""
                        note_text = f" - {f['format_note']}" if f['format_note'] else ""
                        format_options.append(f"{f['resolution']}{note_text} {size_text}")
                    
                    selected_index = st.selectbox(
                        "Select Quality:",
                        range(len(format_options)),
                        format_func=lambda x: format_options[x],
                        key=f"format_{i}",
                        index=len(format_options)-1  # Default to highest quality
                    )
                    st.session_state.format_selections[new_url] = formats[selected_index]['format_id']
                else:
                    st.info("ℹ️ Will download in best available quality")
        
        with col2:
            if len(st.session_state.url_list) > 1:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.url_list.pop(i)
                    st.rerun()

    if st.button("➕ Add Another Video"):
        st.session_state.url_list.append("")
        st.rerun()

    # Show video list and download section
    if st.session_state.url_list and any(st.session_state.url_list):
        st.markdown("---")
        st.subheader("Videos to Download")
        
        # Count valid URLs
        valid_urls = [url for url in st.session_state.url_list if url.strip()]
        st.write(f"{len(valid_urls)} video(s) ready to download")
        
        # Show video information
        for url in valid_urls:
            title, thumbnail_url, _ = get_video_info(url)
            if title and thumbnail_url:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.image(thumbnail_url, width=100)
                with col2:
                    st.write(title)
                    # Add progress bar for this video
                    if f'progress_{url}' in st.session_state:
                        st.progress(st.session_state[f'progress_{url}'])
        
        # Download All button
        if st.button("⬇️ Download All Videos"):
            for url in valid_urls:
                format_id = st.session_state.format_selections.get(url)
                success, filename, file_content = download_video(url, audio_only, format_id)
                
                if success:
                    # Store the downloaded content in session state
                    st.session_state[f'download_{url}'] = {
                        'filename': filename,
                        'content': file_content
                    }
                    
                    # Show save button for this video
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.success(f"✅ {filename} downloaded successfully!")
                    with col2:
                        st.download_button(
                            "💾 Save",
                            data=file_content,
                            file_name=filename,
                            mime="application/octet-stream"
                        )

if __name__ == "__main__":
    main()
