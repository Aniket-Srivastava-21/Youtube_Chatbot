import os
import subprocess
import glob
from urllib.parse import urlparse, parse_qs

def _extract_video_id(video_url: str) -> str:
    """Extract YouTube video id from common URL forms."""
    if not video_url:
        return ""
    parsed = urlparse(video_url)
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        qs = parse_qs(parsed.query)
        return qs.get("v", [""])[0]
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    # fallback: last path segment
    return video_url.split("v=")[-1].split("&")[0]

def _find_subtitle_file(video_id: str, output_dir: str):
    """Find .vtt or .srt file for the given video_id in output_dir."""
    patterns = [os.path.join(output_dir, f"{video_id}.*"),
                os.path.join(output_dir, f"{video_id}_*.*")]
    candidates = []
    for p in patterns:
        candidates.extend(glob.glob(p))
    # prefer vtt then srt then any
    for ext in (".vtt", ".srt"):
        for c in candidates:
            if c.lower().endswith(ext):
                return c
    return candidates[0] if candidates else None

def download_transcript(video_url: str, lang: str = "en", output_dir: str = "transcripts") -> str | None:
    """
    Use yt-dlp to download subtitles for a YouTube video.
    Returns the path to the downloaded subtitle file (vtt/srt) or None on failure.

    Notes:
    - Requires yt-dlp installed and available on PATH.
    - Tries auto-generated subtitles first, falls back to normal subtitles.
    """
    os.makedirs(output_dir, exist_ok=True)
    video_id = _extract_video_id(video_url)
    if not video_id:
        return None

    # output template: store as <video_id>.<ext>
    out_template = os.path.join(output_dir, f"{video_id}.%(ext)s")

    def _run_yt_dlp(args):
        try:
            completed = subprocess.run(
                ["yt-dlp"] + args + [video_url],
                capture_output=True,
                text=True,
                check=False
            )
            return completed.returncode == 0
        except FileNotFoundError:
            raise RuntimeError("yt-dlp not found. Install yt-dlp and ensure it's on PATH.")

    # Try auto-generated subtitles (better coverage)
    args = [
        "--skip-download",
        "--write-auto-sub",
        "--sub-lang", lang,
        "--sub-format", "vtt",
        "-o", out_template,
    ]
    ok = _run_yt_dlp(args)

    # If that failed, try regular subtitles (if provided)
    if not ok:
        args = [
            "--skip-download",
            "--write-sub",
            "--sub-lang", lang,
            "--sub-format", "vtt",
            "-o", out_template,
        ]
        ok = _run_yt_dlp(args)

    if not ok:
        return None

    # locate the downloaded file (prefer .vtt then .srt)
    subtitle_file = _find_subtitle_file(video_id, output_dir)
    return subtitle_file

def extract_transcript(video_url: str, file_path: str) -> str | None:
    """
    Compatibility helper: download subtitles and save plain text to file_path.
    Returns file_path on success, None on failure.
    """
    sub_file = download_transcript(video_url)
    if not sub_file:
        return None

    # convert vtt/srt -> plain text by stripping timestamps
    try:
        with open(sub_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # skip typical VTT/SRT timing lines and numeric counters
            if not line or line.isdigit() or ("-->" in line) or line.lower().startswith("webvtt"):
                continue
            cleaned_lines.append(line)
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as out:
            out.write("\n".join(cleaned_lines))
        return file_path
    except Exception:
        return None