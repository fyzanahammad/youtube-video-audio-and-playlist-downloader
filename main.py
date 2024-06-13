from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pytube import YouTube, Playlist
from moviepy.editor import AudioFileClip
import os

app = FastAPI()

# Initialize download directory
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

class VideoDownloadRequest(BaseModel):
    url: str
    audio_only: bool = False
    resolution: Optional[str] = None
    convert_to_mp3: bool = False

class PlaylistDownloadRequest(BaseModel):
    playlist_url: str
    audio_only: bool = False
    resolution: Optional[str] = None
    convert_to_mp3: bool = False

def download_video(link, audio_only=False, resolution=None, convert_to_mp3=False):
    try:
        yt = YouTube(link)
        if audio_only:
            stream = yt.streams.filter(only_audio=True).first()
        else:
            if resolution:
                stream = yt.streams.filter(res=resolution, progressive=True).first()
                if not stream:
                    stream = yt.streams.get_highest_resolution()
            else:
                stream = yt.streams.get_highest_resolution()

        file_path = stream.download(output_path=DOWNLOAD_DIR)

        if convert_to_mp3:
            mp3_file_path = os.path.splitext(file_path)[0] + '.mp3'
            audio = AudioFileClip(file_path)
            audio.write_audiofile(mp3_file_path, codec='libmp3lame')
            os.remove(file_path)
            file_path = mp3_file_path

        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def download_playlist(playlist_url, audio_only=False, resolution=None, convert_to_mp3=False):
    try:
        playlist = Playlist(playlist_url)
        downloaded_files = []
        for video_url in playlist.video_urls:
            file_path = download_video(video_url, audio_only, resolution, convert_to_mp3)
            if file_path:
                downloaded_files.append(file_path)
        return downloaded_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download_video")
async def download_video_endpoint(request: VideoDownloadRequest, background_tasks: BackgroundTasks):
    file_path = download_video(request.url, request.audio_only, request.resolution, request.convert_to_mp3)
    background_tasks.add_task(os.remove, file_path)
    return {"file_path": file_path, "file_name": os.path.basename(file_path)}

@app.post("/download_playlist")
async def download_playlist_endpoint(request: PlaylistDownloadRequest, background_tasks: BackgroundTasks):
    downloaded_files = download_playlist(request.playlist_url, request.audio_only, request.resolution, request.convert_to_mp3)
    for file_path in downloaded_files:
        background_tasks.add_task(os.remove, file_path)
    return [{"file_path": file_path, "file_name": os.path.basename(file_path)} for file_path in downloaded_files]

@app.get("/downloaded_file")
async def get_downloaded_file(file_path: str):
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/octet-stream", filename=os.path.basename(file_path))
    raise HTTPException(status_code=404, detail="File not found")
