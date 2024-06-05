import streamlit as st
from pytube import YouTube, Playlist
from pytube.cli import on_progress
from tqdm import tqdm
import os

# Initialize session state if not already initialized
if 'downloaded_files' not in st.session_state:
    st.session_state['downloaded_files'] = []

def download_video(link, audio_only=False, resolution=None):
    try:
        yt = YouTube(link, on_progress_callback=on_progress)
        if audio_only:
            stream = yt.streams.filter(only_audio=True).first()
            st.write(f"Downloading audio for {yt.title}...")
        else:
            if resolution:
                stream = yt.streams.filter(res=resolution, progressive=True).first()
                if not stream:
                    stream = yt.streams.get_highest_resolution()
                    st.warning(f"Requested resolution {resolution} not available for {yt.title}. Downloading highest available resolution.")
            else:
                stream = yt.streams.get_highest_resolution()
            st.write(f"Downloading {yt.title} at {resolution or 'highest available'} resolution...")
        output_path = 'downloads'
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        file_path = stream.download(output_path=output_path)
        st.write(f"{yt.title} downloaded successfully.")
        return file_path
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def download_playlist(playlist_url, audio_only=False, resolution=None):
    try:
        playlist = Playlist(playlist_url)
        downloaded_files = []
        for video_url in tqdm(playlist.video_urls):
            file_path = download_video(video_url, audio_only, resolution)
            if file_path:
                downloaded_files.append(file_path)
        st.write("All videos in the playlist downloaded successfully!")
        return downloaded_files
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

def main():
    st.title("YouTube Video Downloader")

    quality_options = ["144p", "240p", "360p", "480p", "720p", "1080p"]

    # Create columns for options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        option = st.selectbox("Select download option", ("Individual Videos", "Playlist"))

    with col2:
        download_type = st.selectbox("Download type", ("Video", "Audio Only"))

    with col3:
        resolution = st.selectbox("Select video quality", quality_options)

    if option == "Individual Videos":
        st.write("Enter the YouTube video URLs:")
        urls = st.text_area("Enter URLs (one per line):", height=200)
        urls = [url.strip() for url in urls.split('\n') if url.strip()]
    else:
        st.write("Enter the YouTube playlist URL:")
        playlist_url = st.text_input("Enter Playlist URL")

    if st.button("Download"):
        st.write("Downloading...")
        downloaded_files = []

        if option == "Individual Videos":
            for url in tqdm(urls):
                if url:
                    file_path = download_video(url, audio_only=(download_type == "Audio Only"), resolution=resolution)
                    if file_path:
                        downloaded_files.append(file_path)
                        st.session_state['downloaded_files'].append(file_path)
        else:
            downloaded_files = download_playlist(playlist_url, audio_only=(download_type == "Audio Only"), resolution=resolution)
            for file_path in downloaded_files:
                if file_path:
                    st.session_state['downloaded_files'].append(file_path)

        st.write("All downloads completed!")

    # Display download buttons for all downloaded files individually
    for file_path in st.session_state['downloaded_files']:
        with open(file_path, "rb") as file:
            st.download_button(
                label=f"Download {os.path.basename(file_path)}",
                data=file,
                file_name=os.path.basename(file_path),
                mime="application/octet-stream"
            )

if __name__ == "__main__":
    main()
