import motor.motor_asyncio
from config import Config
from .utils import send_log

class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.user

    def new_user(self, id):
        return dict(
            _id=int(id),                                   
            file_id=None,
            caption=None,
            rename_mode='manual',  # 'manual' or 'auto'
            upload_channel=None,  # Channel ID for uploads
            always_ask=True,  # Always ask before renaming
            upload_as='document',  # 'document', 'video', or 'audio'
            # Auto detection settings
            auto_detect_type=True,
            auto_detect_language=True,
            auto_detect_year=True,
            auto_detect_quality=True,
            auto_detect_source=True,
            auto_detect_ott=True,
            auto_detect_encoding=True,
            auto_detect_audio=True,
            # Customization settings
            remove_words=[],
            replace_words={},
            quality_format='keep',  # 'keep', 'remove', or specific like '1080p'
            prefix='',
            suffix='',
            auto_clean=True
        )

    async def add_user(self, b, m):
        try:
            u = m.from_user
            if not await self.is_user_exist(u.id):
                user = self.new_user(u.id)
                await self.col.insert_one(user)            
                await send_log(b, u)
        except Exception as e:
            print(f"Error adding user: {e}")

    async def is_user_exist(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return bool(user)
        except Exception as e:
            print(f"Error checking user existence: {e}")
            return False

    async def total_users_count(self):
        try:
            count = await self.col.count_documents({})
            return count
        except Exception as e:
            print(f"Error counting users: {e}")
            return 0

    async def get_all_users(self):
        try:
            all_users = self.col.find({})
            return all_users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    async def delete_user(self, user_id):
        try:
            await self.col.delete_many({'_id': int(user_id)})
        except Exception as e:
            print(f"Error deleting user: {e}")
    
    async def set_thumbnail(self, id, file_id):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})
        except Exception as e:
            print(f"Error setting thumbnail: {e}")

    async def get_thumbnail(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('file_id', None) if user else None
        except Exception as e:
            print(f"Error getting thumbnail: {e}")
            return None

    async def set_caption(self, id, caption):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})
        except Exception as e:
            print(f"Error setting caption: {e}")

    async def get_caption(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('caption', None) if user else None
        except Exception as e:
            print(f"Error getting caption: {e}")
            return None

    # Rename mode settings
    async def set_rename_mode(self, id, mode):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'rename_mode': mode}})
        except Exception as e:
            print(f"Error setting rename mode: {e}")

    async def get_rename_mode(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('rename_mode', 'manual') if user else 'manual'
        except Exception as e:
            print(f"Error getting rename mode: {e}")
            return 'manual'

    # Upload settings
    async def set_upload_channel(self, id, channel_id):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'upload_channel': channel_id}})
        except Exception as e:
            print(f"Error setting upload channel: {e}")

    async def get_upload_channel(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('upload_channel', None) if user else None
        except Exception as e:
            print(f"Error getting upload channel: {e}")
            return None

    async def set_always_ask(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'always_ask': value}})
        except Exception as e:
            print(f"Error setting always ask: {e}")

    async def get_always_ask(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('always_ask', True) if user else True
        except Exception as e:
            print(f"Error getting always ask: {e}")
            return True

    async def set_upload_as(self, id, upload_type):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'upload_as': upload_type}})
        except Exception as e:
            print(f"Error setting upload type: {e}")

    async def get_upload_as(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('upload_as', 'document') if user else 'document'
        except Exception as e:
            print(f"Error getting upload type: {e}")
            return 'document'

    # Auto detection settings
    async def set_auto_detect_type(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_type': value}})
        except Exception as e:
            print(f"Error setting auto detect type: {e}")

    async def get_auto_detect_type(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_type', True) if user else True
        except Exception as e:
            return True

    async def set_auto_detect_language(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_language': value}})
        except Exception as e:
            print(f"Error setting auto detect language: {e}")

    async def get_auto_detect_language(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_language', True) if user else True
        except Exception as e:
            return True

    async def set_auto_detect_year(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_year': value}})
        except Exception as e:
            print(f"Error setting auto detect year: {e}")

    async def get_auto_detect_year(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_year', True) if user else True
        except Exception as e:
            return True

    async def set_auto_detect_quality(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_quality': value}})
        except Exception as e:
            print(f"Error setting auto detect quality: {e}")

    async def get_auto_detect_quality(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_quality', True) if user else True
        except Exception as e:
            return True

    async def set_auto_detect_source(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_source': value}})
        except Exception as e:
            print(f"Error setting auto detect source: {e}")

    async def get_auto_detect_source(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_source', True) if user else True
        except Exception as e:
            return True

    async def set_auto_detect_ott(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_ott': value}})
        except Exception as e:
            print(f"Error setting auto detect OTT: {e}")

    async def get_auto_detect_ott(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_ott', True) if user else True
        except Exception as e:
            return True

    async def set_auto_detect_encoding(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_encoding': value}})
        except Exception as e:
            print(f"Error setting auto detect encoding: {e}")

    async def get_auto_detect_encoding(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_encoding', True) if user else True
        except Exception as e:
            return True

    async def set_auto_detect_audio(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_audio': value}})
        except Exception as e:
            print(f"Error setting auto detect audio: {e}")

    async def get_auto_detect_audio(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_detect_audio', True) if user else True
        except Exception as e:
            return True

    # Customization settings
    async def set_remove_words(self, id, words_list):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'remove_words': words_list}})
        except Exception as e:
            print(f"Error setting remove words: {e}")

    async def get_remove_words(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('remove_words', []) if user else []
        except Exception as e:
            return []

    async def set_replace_words(self, id, replace_dict):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'replace_words': replace_dict}})
        except Exception as e:
            print(f"Error setting replace words: {e}")

    async def get_replace_words(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('replace_words', {}) if user else {}
        except Exception as e:
            return {}

    async def set_quality_format(self, id, quality):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'quality_format': quality}})
        except Exception as e:
            print(f"Error setting quality format: {e}")

    async def get_quality_format(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('quality_format', 'keep') if user else 'keep'
        except Exception as e:
            return 'keep'

    async def set_prefix(self, id, prefix):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})
        except Exception as e:
            print(f"Error setting prefix: {e}")

    async def get_prefix(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('prefix', '') if user else ''
        except Exception as e:
            return ''

    async def set_suffix(self, id, suffix):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})
        except Exception as e:
            print(f"Error setting suffix: {e}")

    async def get_suffix(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('suffix', '') if user else ''
        except Exception as e:
            return ''

    async def set_auto_clean(self, id, value):
        try:
            await self.col.update_one({'_id': int(id)}, {'$set': {'auto_clean': value}})
        except Exception as e:
            print(f"Error setting auto clean: {e}")

    async def get_auto_clean(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            return user.get('auto_clean', True) if user else True
        except Exception as e:
            return True

    # Get all settings at once
    async def get_all_rename_settings(self, id):
        try:
            user = await self.col.find_one({'_id': int(id)})
            if user:
                return {
                    'rename_mode': user.get('rename_mode', 'manual'),
                    'upload_channel': user.get('upload_channel', None),
                    'always_ask': user.get('always_ask', True),
                    'upload_as': user.get('upload_as', 'document'),
                    'auto_detect_type': user.get('auto_detect_type', True),
                    'auto_detect_language': user.get('auto_detect_language', True),
                    'auto_detect_year': user.get('auto_detect_year', True),
                    'auto_detect_quality': user.get('auto_detect_quality', True),
                    'auto_detect_source': user.get('auto_detect_source', True),
                    'auto_detect_ott': user.get('auto_detect_ott', True),
                    'auto_detect_encoding': user.get('auto_detect_encoding', True),
                    'auto_detect_audio': user.get('auto_detect_audio', True),
                    'remove_words': user.get('remove_words', []),
                    'replace_words': user.get('replace_words', {}),
                    'quality_format': user.get('quality_format', 'keep'),
                    'prefix': user.get('prefix', ''),
                    'suffix': user.get('suffix', ''),
                    'auto_clean': user.get('auto_clean', True)
                }
            return None
        except Exception as e:
            print(f"Error getting all rename settings: {e}")
            return None


db = Database(Config.DB_URL, Config.DB_NAME)
