import streamlit as st
from pytube import YouTube, Playlist
from tqdm import tqdm
import os

# Initialize session state if not already initialized
if 'downloaded_files' not in st.session_state:
    st.session_state['downloaded_files'] = []

def download_video(link, audio_only=False):
    try:
        yt = YouTube(link)
        if audio_only:
            stream = yt.streams.filter(only_audio=True).first()
            st.write(f"Downloading audio for {yt.title}...")
        else:
            stream = yt.streams.get_highest_resolution()
            st.write(f"Downloading {yt.title}...")
        output_path = 'downloads'
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        file_path = stream.download(output_path=output_path)
        st.write(f"{yt.title} downloaded successfully.")
        return file_path
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def download_playlist(playlist_url, audio_only=False):
    try:
        playlist = Playlist(playlist_url)
        downloaded_files = []
        for video_url in tqdm(playlist.video_urls):
            file_path = download_video(video_url, audio_only)
            if file_path:
                downloaded_files.append(file_path)
        st.write("All videos in the playlist downloaded successfully!")
        return downloaded_files
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

def main():
    st.title("YouTube Video Downloader")
    option = st.radio("Select download option", ("Individual Videos", "Playlist"))

    if option == "Individual Videos":
        st.write("Enter the YouTube video URLs:")
        urls = st.text_area("Enter URLs (one per line):", height=200)
        urls = urls.split('\n')
        download_type = st.radio("Download type", ("Video", "Audio Only"))
        if st.button("Download"):
            st.write("Downloading...")
            downloaded_files = []
            for url in tqdm(urls):
                if url.strip():
                    file_path = download_video(url, audio_only=(download_type == "Audio Only"))
                    if file_path:
                        downloaded_files.append(file_path)
                        st.session_state['downloaded_files'].append(file_path)
            st.write("All downloads completed!")
    else:
        st.write("Enter the YouTube playlist URL:")
        playlist_url = st.text_input("Enter Playlist URL")
        download_type = st.radio("Download type", ("Video", "Audio Only"))
        if st.button("Download"):
            st.write("Downloading playlist...")
            downloaded_files = download_playlist(playlist_url, audio_only=(download_type == "Audio Only"))
            for file_path in downloaded_files:
                if file_path:
                    st.session_state['downloaded_files'].append(file_path)

    # Display download buttons for all downloaded files
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
