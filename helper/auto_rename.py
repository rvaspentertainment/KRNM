import re
from pyrogram.enums import MessageMediaType

# Common unwanted words to remove
COMMON_JUNK_WORDS = [
    'www', 'http', 'https', 'download', 'movies', 'movie', 'film', 'films',
    'torrent', 'torrents', 'hdcam', 'hdts', 'hdtc', 'camrip', 'cam', 
    'dvdrip', 'dvdscr', 'brrip', 'bluray', 'webrip', 'web-dl', 'webdl',
    'x264', 'x265', 'h264', 'h265', 'hevc', '10bit', '8bit',
    'esub', 'esubs', 'msub', 'msubs', 'hindi', 'english', 'tamil', 'telugu',
    'dual', 'audio', 'multi', 'aac', 'dd5.1', 'dd+', 'atmos',
    'sample', 'rarbg', 'yts', 'yify', 'etrg', 'shaanig', 'pahe'
]

# Language keywords
LANGUAGE_KEYWORDS = {
    'hindi': ['hindi', 'hin', 'हिंदी'],
    'english': ['english', 'eng'],
    'tamil': ['tamil', 'tam', 'தமிழ்'],
    'telugu': ['telugu', 'tel', 'తెలుగు'],
    'malayalam': ['malayalam', 'mal', 'മലയാളം'],
    'kannada': ['kannada', 'kan', 'ಕನ್ನಡ'],
    'bengali': ['bengali', 'ben', 'বাংলা'],
    'marathi': ['marathi', 'mar', 'मराठी'],
    'punjabi': ['punjabi', 'pun', 'ਪੰਜਾਬੀ'],
    'gujarati': ['gujarati', 'guj', 'ગુજરાતી']
}

# Quality patterns
QUALITY_PATTERNS = [
    '2160p', '1080p', '720p', '480p', '360p', '240p', '144p',
    '4k', '2k', 'uhd', 'fhd', 'hd', 'sd'
]


def detect_language(filename):
    """Detect language from filename"""
    filename_lower = filename.lower()
    detected_languages = []
    
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in filename_lower:
                if lang not in detected_languages:
                    detected_languages.append(lang)
    
    return detected_languages


def detect_quality(filename):
    """Detect quality from filename"""
    filename_lower = filename.lower()
    
    for quality in QUALITY_PATTERNS:
        if quality in filename_lower:
            return quality.upper()
    
    return None


def detect_media_type(file, media_type):
    """Detect if file is video or audio"""
    if media_type == MessageMediaType.VIDEO:
        return 'video'
    elif media_type == MessageMediaType.AUDIO:
        return 'audio'
    elif media_type == MessageMediaType.DOCUMENT:
        # Check by extension
        if hasattr(file, 'file_name') and file.file_name:
            ext = file.file_name.rsplit('.', 1)[-1].lower()
            video_exts = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'webm', 'm4v', '3gp']
            audio_exts = ['mp3', 'aac', 'flac', 'wav', 'ogg', 'm4a', 'wma', 'opus']
            
            if ext in video_exts:
                return 'video'
            elif ext in audio_exts:
                return 'audio'
    
    return 'unknown'


def extract_movie_name(filename):
    """Extract main movie/show name from filename"""
    # Remove extension
    name = filename.rsplit('.', 1)[0]
    
    # Remove year if present
    name = re.sub(r'\(?\d{4}\)?', '', name)
    
    # Remove quality
    for quality in QUALITY_PATTERNS:
        name = re.sub(quality, '', name, flags=re.IGNORECASE)
    
    # Remove common junk words
    for junk in COMMON_JUNK_WORDS:
        name = re.sub(rf'\b{junk}\b', '', name, flags=re.IGNORECASE)
    
    # Remove brackets and their contents
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\{.*?\}', '', name)
    
    # Clean up separators
    name = re.sub(r'[._-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def clean_filename(filename, remove_words=None, replace_words=None, auto_clean=True):
    """Clean filename by removing/replacing words"""
    name = filename
    
    # Auto clean common junk
    if auto_clean:
        for junk in COMMON_JUNK_WORDS:
            name = re.sub(rf'\b{junk}\b', '', name, flags=re.IGNORECASE)
    
    # Remove custom words
    if remove_words:
        for word in remove_words:
            name = re.sub(rf'\b{word}\b', '', name, flags=re.IGNORECASE)
    
    # Replace custom words
    if replace_words:
        for old_word, new_word in replace_words.items():
            name = re.sub(rf'\b{old_word}\b', new_word, name, flags=re.IGNORECASE)
    
    # Clean up
    name = re.sub(r'[._-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


async def auto_rename_file(filename, settings, media_type, file):
    """Main function to auto-rename file based on settings"""
    
    # Get extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
    else:
        name = filename
        ext = 'mkv'  # default
    
    # Extract movie name
    clean_name = extract_movie_name(filename)
    
    # Clean filename
    clean_name = clean_filename(
        clean_name,
        remove_words=settings.get('remove_words', []),
        replace_words=settings.get('replace_words', {}),
        auto_clean=settings.get('auto_clean', True)
    )
    
    # Detect and add language
    if settings.get('auto_detect_language', True):
        languages = detect_language(filename)
        if languages:
            lang_str = '+'.join([l.capitalize() for l in languages])
            clean_name = f"{clean_name} {lang_str}"
    
    # Detect and add quality
    quality_setting = settings.get('quality_format', 'keep')
    if quality_setting == 'keep':
        quality = detect_quality(filename)
        if quality:
            clean_name = f"{clean_name} {quality}"
    elif quality_setting != 'remove':
        # Add specific quality
        clean_name = f"{clean_name} {quality_setting}"
    
    # Detect and add media type
    if settings.get('auto_detect_type', True):
        media = detect_media_type(file, media_type)
        if media == 'video':
            clean_name = f"{clean_name}"  # Can add [Video] if needed
        elif media == 'audio':
            clean_name = f"{clean_name} [Audio]"
    
    # Add prefix
    prefix = settings.get('prefix', '')
    if prefix:
        clean_name = f"{prefix} {clean_name}"
    
    # Add suffix
    suffix = settings.get('suffix', '')
    if suffix:
        clean_name = f"{clean_name} {suffix}"
    
    # Clean up final name
    clean_name = re.sub(r'\s+', '.', clean_name.strip())
    clean_name = re.sub(r'\.+', '.', clean_name)
    
    # Add extension
    new_filename = f"{clean_name}.{ext}"
    
    return new_filename
