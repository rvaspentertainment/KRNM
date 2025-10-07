import re
from pyrogram.enums import MessageMediaType

# Common unwanted words to remove
COMMON_JUNK_WORDS = [
    'www', 'http', 'https', 'download', 'movies', 'movie', 'film', 'films',
    'torrent', 'torrents', 'sample', 'rarbg', 'yts', 'yify', 'etrg', 'shaanig', 
    'pahe', 'mkvcage', 'tamilrockers', 'tamilblasters', 'telegram', 'encoded',
    'filmywap', 'worldfree4u', 'moviesda', 'isaimini', 'kuttymovies'
]

# Video quality and encoding patterns
QUALITY_PATTERNS = {
    '2160p': ['2160p', '4k', 'uhd', '4kuhd'],
    '1080p': ['1080p', 'fhd', 'fullhd'],
    '720p': ['720p', 'hd'],
    '480p': ['480p', 'sd'],
    '360p': ['360p'],
    '240p': ['240p']
}

# Encoding patterns
ENCODING_PATTERNS = {
    'H264': ['h264', 'h.264', 'x264', 'x.264', 'avc'],
    'H265': ['h265', 'h.265', 'x265', 'x.265', 'hevc'],
    '10bit': ['10bit', '10-bit'],
    '8bit': ['8bit', '8-bit']
}

# Source patterns
SOURCE_PATTERNS = {
    'WEB-DL': ['web-dl', 'webdl', 'web.dl'],
    'WEBRip': ['webrip', 'web-rip', 'web.rip'],
    'HDRip': ['hdrip', 'hd-rip', 'hd.rip'],
    'DVDRip': ['dvdrip', 'dvd-rip', 'dvd.rip'],
    'BluRay': ['bluray', 'blu-ray', 'brrip', 'bdrip'],
    'HDTV': ['hdtv', 'hdtvrip'],
    'TVRip': ['tvrip', 'tv-rip'],
    'HDCAM': ['hdcam', 'hd-cam'],
    'CAMRip': ['camrip', 'cam-rip', 'cam']
}

# OTT Platform patterns
OTT_PLATFORMS = {
    'Netflix': ['nf', 'netflix', 'ntflx'],
    'Amazon': ['amzn', 'amazon', 'prime', 'primevideo'],
    'Disney+': ['dsnp', 'disney', 'disneyplus', 'disney+'],
    'Hotstar': ['hotstar', 'dplus', 'd+'],
    'HBO': ['hbo', 'hbomax', 'hbo+'],
    'Apple': ['atvp', 'apple', 'appletv', 'atv'],
    'Hulu': ['hulu'],
    'ZEE5': ['zee5', 'zee'],
    'SonyLIV': ['sonyliv', 'sony'],
    'Voot': ['voot'],
    'MX': ['mx', 'mxplayer'],
    'Aha': ['aha'],
    'Sun': ['sunnxt', 'sun']
}

# Language keywords
LANGUAGE_KEYWORDS = {
    'Hindi': ['hindi', 'hin', 'हिंदी'],
    'English': ['english', 'eng'],
    'Tamil': ['tamil', 'tam', 'தமிழ்'],
    'Telugu': ['telugu', 'tel', 'తెలుగు'],
    'Malayalam': ['malayalam', 'mal', 'മലയാളം'],
    'Kannada': ['kannada', 'kan', 'ಕನ್ನಡ'],
    'Bengali': ['bengali', 'ben', 'বাংলা'],
    'Marathi': ['marathi', 'mar', 'मराठी'],
    'Punjabi': ['punjabi', 'pun', 'ਪੰਜਾਬੀ'],
    'Gujarati': ['gujarati', 'guj', 'ગુજરાતી'],
    'Multi': ['multi', 'dual', 'dualaud', 'dual-audio']
}

# Audio patterns
AUDIO_PATTERNS = {
    'AAC': ['aac', 'aac2.0'],
    'AC3': ['ac3', 'dd', 'dd5.1', 'dd+'],
    'DTS': ['dts', 'dts-hd'],
    'Atmos': ['atmos', 'dd+atmos'],
    'TrueHD': ['truehd']
}


def extract_year(filename):
    """Extract year from filename"""
    try:
        # Match 4-digit year (1900-2099)
        match = re.search(r'\b(19\d{2}|20\d{2})\b', filename)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error extracting year: {e}")
    return None


def detect_quality(filename):
    """Detect quality from filename"""
    try:
        filename_lower = filename.lower()
        for quality, patterns in QUALITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return quality
    except Exception as e:
        print(f"Error detecting quality: {e}")
    return None


def detect_encoding(filename):
    """Detect encoding from filename"""
    try:
        filename_lower = filename.lower()
        for encoding, patterns in ENCODING_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return encoding
    except Exception as e:
        print(f"Error detecting encoding: {e}")
    return None


def detect_source(filename):
    """Detect source from filename"""
    try:
        filename_lower = filename.lower()
        for source, patterns in SOURCE_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return source
    except Exception as e:
        print(f"Error detecting source: {e}")
    return None


def detect_ott(filename):
    """Detect OTT platform from filename"""
    try:
        filename_lower = filename.lower()
        for platform, patterns in OTT_PLATFORMS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return platform
    except Exception as e:
        print(f"Error detecting OTT: {e}")
    return None


def detect_audio(filename):
    """Detect audio format from filename"""
    try:
        filename_lower = filename.lower()
        detected = []
        for audio, patterns in AUDIO_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    if audio not in detected:
                        detected.append(audio)
        return detected
    except Exception as e:
        print(f"Error detecting audio: {e}")
    return []


def detect_languages(filename):
    """Detect languages from filename"""
    try:
        filename_lower = filename.lower()
        detected_languages = []
        
        for lang, keywords in LANGUAGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    if lang not in detected_languages:
                        detected_languages.append(lang)
        
        return detected_languages
    except Exception as e:
        print(f"Error detecting languages: {e}")
    return []


def detect_media_type(file, media_type):
    """Detect if file is video or audio"""
    try:
        if media_type == MessageMediaType.VIDEO:
            return 'Video'
        elif media_type == MessageMediaType.AUDIO:
            return 'Audio'
        elif media_type == MessageMediaType.DOCUMENT:
            if hasattr(file, 'file_name') and file.file_name:
                ext = file.file_name.rsplit('.', 1)[-1].lower()
                video_exts = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'webm', 'm4v', '3gp', 'ts']
                audio_exts = ['mp3', 'aac', 'flac', 'wav', 'ogg', 'm4a', 'wma', 'opus']
                
                if ext in video_exts:
                    return 'Video'
                elif ext in audio_exts:
                    return 'Audio'
    except Exception as e:
        print(f"Error detecting media type: {e}")
    return None


def extract_movie_name(filename):
    """Extract main movie/show name from filename - CLEAN VERSION"""
    try:
        # Remove extension
        name = filename.rsplit('.', 1)[0]
        
        # Remove everything in brackets first
        name = re.sub(r'\[.*?\]', '', name)
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'\{.*?\}', '', name)
        
        # Remove year
        name = re.sub(r'\b(19\d{2}|20\d{2})\b', '', name)
        
        # Remove quality patterns
        name = re.sub(r'\b(2160p|1080p|720p|480p|360p|240p|4k|uhd|fhd|hd|sd)\b', '', name, flags=re.IGNORECASE)
        
        # Remove encoding
        name = re.sub(r'\b(h264|h265|x264|x265|hevc|avc|10bit|8bit)\b', '', name, flags=re.IGNORECASE)
        
        # Remove source
        name = re.sub(r'\b(web-?dl|webrip|hdrip|dvdrip|bluray|blu-?ray|brrip|bdrip|hdtv|tvrip|hdcam|camrip|cam)\b', '', name, flags=re.IGNORECASE)
        
        # Remove OTT platforms
        name = re.sub(r'\b(netflix|nf|ntflx|amazon|amzn|prime|disney|hotstar|hbo|apple|hulu|zee5|sonyliv|voot|mx)\b', '', name, flags=re.IGNORECASE)
        
        # Remove audio
        name = re.sub(r'\b(aac|ac3|dd|dts|atmos|truehd)\b', '', name, flags=re.IGNORECASE)
        
        # Remove common junk
        for junk in COMMON_JUNK_WORDS:
            name = re.sub(rf'\b{junk}\b', '', name, flags=re.IGNORECASE)
        
        # Remove special characters
        name = re.sub(r'[#@\[\]\{\}_]', '', name)
        
        # Clean up separators
        name = re.sub(r'[.-]+', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()
    except Exception as e:
        print(f"Error extracting movie name: {e}")
        return filename.rsplit('.', 1)[0]

def clean_filename(filename, remove_words=None, replace_words=None, auto_clean=True):
    """Clean filename by removing/replacing words and unwanted characters"""
    try:
        name = filename
        
        # Auto clean common junk
        if auto_clean:
            for junk in COMMON_JUNK_WORDS:
                name = re.sub(rf'\b{junk}\b', '', name, flags=re.IGNORECASE)
        
        # Remove custom words
        if remove_words:
            for word in remove_words:
                if word:
                    name = re.sub(rf'\b{re.escape(word)}\b', '', name, flags=re.IGNORECASE)
        
        # Replace custom words
        if replace_words:
            for old_word, new_word in replace_words.items():
                if old_word and new_word:
                    name = re.sub(rf'\b{re.escape(old_word)}\b', new_word, name, flags=re.IGNORECASE)
        
        # Remove unwanted special characters
        name = re.sub(r'[#@\[\]\{\}]', '', name)
        
        # Remove brackets and their contents
        name = re.sub(r'\[.*?\]', '', name)
        name = re.sub(r'\(.*?\)', '', name)
        
        # Clean up separators
        name = re.sub(r'[._-]+', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()
    except Exception as e:
        print(f"Error cleaning filename: {e}")
        return filename

async def auto_rename_file(filename, settings, media_type, file):
    """Main function to auto-rename file based on settings"""
    try:
        # Get extension
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
        else:
            name = filename
            ext = 'mkv'  # default
        
        # Start with original filename
        original_name = filename
        
        # Extract movie name
        clean_name = extract_movie_name(filename)
        
        # Clean filename (remove/replace words)
        clean_name = clean_filename(
            clean_name,
            remove_words=settings.get('remove_words', []),
            replace_words=settings.get('replace_words', {}),
            auto_clean=settings.get('auto_clean', True)
        )
        
        # If clean name is empty, use a default
        if not clean_name or len(clean_name.strip()) < 2:
            clean_name = "Renamed_File"
        
        components = [clean_name]
        
        # Detect and add year
        if settings.get('auto_detect_year', True):
            year = extract_year(filename)
            if year:
                components.append(f"({year})")
        
        # Detect and add language
        if settings.get('auto_detect_language', True):
            languages = detect_languages(filename)
            if languages:
                lang_str = '+'.join(languages)
                components.append(lang_str)
        
        # Detect and add quality
        quality_setting = settings.get('quality_format', 'keep')
        if quality_setting == 'keep':
            quality = detect_quality(filename)
            if quality:
                components.append(quality)
        elif quality_setting != 'remove':
            # Add specific quality
            components.append(quality_setting.upper())
        
        # Detect and add source
        if settings.get('auto_detect_source', True):
            source = detect_source(filename)
            if source:
                components.append(source)
        
        # Detect and add OTT
        if settings.get('auto_detect_ott', True):
            ott = detect_ott(filename)
            if ott:
                components.append(ott)
        
        # Detect and add encoding
        if settings.get('auto_detect_encoding', True):
            encoding = detect_encoding(filename)
            if encoding:
                components.append(encoding)
        
        # Detect and add audio
        if settings.get('auto_detect_audio', True):
            audio_list = detect_audio(filename)
            if audio_list:
                components.extend(audio_list)
        
        # Detect and add media type tag
        if settings.get('auto_detect_type', False):
            media = detect_media_type(file, media_type)
            if media == 'Audio':
                components.append('[Audio]')
        
        # Add prefix
        prefix = settings.get('prefix', '')
        if prefix:
            components.insert(0, prefix)
        
        # Add suffix
        suffix = settings.get('suffix', '')
        if suffix:
            components.append(suffix)
        
        # Join all components
        final_name = ' '.join(filter(None, components))
        
        # Clean up final name
        final_name = re.sub(r'\s+', '.', final_name.strip())
        final_name = re.sub(r'\.+', '.', final_name)
        
        # Remove leading/trailing dots
        final_name = final_name.strip('.')
        
        # Add extension
        new_filename = f"{final_name}.{ext}"
        
        return new_filename
    
    except Exception as e:
        print(f"Error in auto_rename_file: {e}")
        return filename
