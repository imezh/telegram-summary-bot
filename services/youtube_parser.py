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

    api = YouTubeTranscriptApi()

    # Try ru/en first, then fall back to any available transcript
    try:
        fetched = api.fetch(video_id, languages=["ru", "en"])
    except (NoTranscriptFound, Exception):
        transcript_list = api.list(video_id)
        transcripts = list(transcript_list)
        if not transcripts:
            raise NoTranscriptFound(video_id, ["ru", "en"], [])
        fetched = transcripts[0].fetch()

    return " ".join(snippet.text for snippet in fetched).strip()
