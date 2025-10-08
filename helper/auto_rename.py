import re
from pyrogram.enums import MessageMediaType

# Common unwanted words to remove
COMMON_JUNK_WORDS = [
    'www', 'http', 'https', 'download', 'movies', 'movie', 'film', 'films',
    'torrent', 'torrents', 'sample', 'rarbg', 'yts', 'yify', 'etrg', 'shaanig', 
    'pahe', 'mkvcage', 'tamilrockers', 'tamilblasters', 'telegram', 'encoded',
    'filmywap', 'worldfree4u', 'moviesda', 'isaimini', 'kuttymovies'
]


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


async def auto_rename_file(filename, settings):
    """Main function to auto-rename file based on settings - SIMPLIFIED VERSION"""
    try:
        # Get extension
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
        else:
            name = filename
            ext = 'mkv'  # default
        
        # Clean filename (remove/replace words only)
        clean_name = clean_filename(
            name,
            remove_words=settings.get('remove_words', []),
            replace_words=settings.get('replace_words', {}),
            auto_clean=settings.get('auto_clean', True)
        )
        
        # If clean name is empty, use a default
        if not clean_name or len(clean_name.strip()) < 2:
            clean_name = "Renamed_File"
        
        components = [clean_name]
        
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
