import re
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled


def _extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(url: str) -> str:
    video_id = _extract_video_id(url)
    if not video_id:
        raise ValueError("Не удалось извлечь ID видео из URL.")

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    # Try manual transcripts first (ru, en), then auto-generated
    try:
        transcript = transcript_list.find_transcript(["ru", "en"])
    except NoTranscriptFound:
        # Fall back to any available transcript (auto-generated)
        transcripts = list(transcript_list)
        if not transcripts:
            raise NoTranscriptFound(video_id, ["ru", "en"], [])
        transcript = transcripts[0]

    entries = transcript.fetch()
    return " ".join(entry["text"] for entry in entries).strip()
