import re

def extract_clean_subtitles(vtt_file):
    subtitle_lines = []
    seen_lines = set()  # Avoid duplicate lines

    with open(vtt_file, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()

            # Skip noise
            if (
                not line
                or line.startswith(("WEBVTT", "Kind:", "Language:"))
                or "-->" in line
                or re.match(r"^\[\w+\]$", line)  # [Music], [Applause], etc.
            ):
                continue

            # Remove tags like <00:00:16.760><c>word</c>
            cleaned_line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}><c>(.*?)</c>", r"\1", line)

            # Avoid duplicates
            if cleaned_line not in seen_lines:
                subtitle_lines.append(cleaned_line)
                seen_lines.add(cleaned_line)

    return " ".join(subtitle_lines)

def get_youtube_video_id(url):
    """
    Extracts the unique video identifier from a YouTube URL.

    Args:
        url (str): The YouTube URL.

    Returns:
        str or None: The video ID if found, otherwise None.
    """
    # Regular expression to match various YouTube URL formats
    # Added raw string literal (r'') to handle backslashes correctly
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')

    match = re.search(youtube_regex, url) # Changed match to search as it's more appropriate for finding the pattern anywhere in the string

    video_id = match.group(6)

    if match:
        return video_id
    return url