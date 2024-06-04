import streamlit as st
from pytube import YouTube, Playlist
from tqdm import tqdm

def download_video(link, audio_only=False):
    try:
        yt = YouTube(link)
        if audio_only:
            stream = yt.streams.filter(only_audio=True).first()
            st.write(f"Downloading audio for {yt.title}...")
        else:
            stream = yt.streams.get_highest_resolution()
            st.write(f"Downloading {yt.title}...")
        stream.download(output_path='downloads')
        st.write(f"{yt.title} downloaded successfully.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def download_playlist(playlist_url, audio_only=False):
    try:
        playlist = Playlist(playlist_url)
        for video_url in tqdm(playlist.video_urls):
            download_video(video_url, audio_only)
        st.write("All videos in the playlist downloaded successfully!")
    except Exception as e:
        st.error(f"An error occurred: {e}")

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
            for url in tqdm(urls):
                if url.strip():
                    download_video(url, audio_only=(download_type == "Audio Only"))
            st.write("All downloads completed!")
    else:
        st.write("Enter the YouTube playlist URL:")
        playlist_url = st.text_input("Enter Playlist URL")
        download_type = st.radio("Download type", ("Video", "Audio Only"))
        if st.button("Download"):
            st.write("Downloading playlist...")
            download_playlist(playlist_url, audio_only=(download_type == "Audio Only"))

if __name__ == "__main__":
    main()