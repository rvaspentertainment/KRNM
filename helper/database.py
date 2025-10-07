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
            auto_detect_type=True,  # Auto detect video/audio
            auto_detect_language=True,  # Auto detect language
            remove_words=[],  # Words to remove from filename
            replace_words={},  # Words to replace {old: new}
            quality_format='keep',  # 'keep', 'remove', or specific like '1080p'
            prefix='',  # Add prefix to filename
            suffix='',  # Add suffix to filename
            auto_clean=True  # Remove common unwanted words
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)            
            await send_log(b, u)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        await self.col.delete_many({'_id': int(user_id)})
    
    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('file_id', None)

    async def set_caption(self, id, caption):
        await self.col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('caption', None)

    # New methods for auto-rename feature
    async def set_rename_mode(self, id, mode):
        await self.col.update_one({'_id': int(id)}, {'$set': {'rename_mode': mode}})

    async def get_rename_mode(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('rename_mode', 'manual')

    async def set_auto_detect_type(self, id, value):
        await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_type': value}})

    async def get_auto_detect_type(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('auto_detect_type', True)

    async def set_auto_detect_language(self, id, value):
        await self.col.update_one({'_id': int(id)}, {'$set': {'auto_detect_language': value}})

    async def get_auto_detect_language(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('auto_detect_language', True)

    async def set_remove_words(self, id, words_list):
        await self.col.update_one({'_id': int(id)}, {'$set': {'remove_words': words_list}})

    async def get_remove_words(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('remove_words', [])

    async def set_replace_words(self, id, replace_dict):
        await self.col.update_one({'_id': int(id)}, {'$set': {'replace_words': replace_dict}})

    async def get_replace_words(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('replace_words', {})

    async def set_quality_format(self, id, quality):
        await self.col.update_one({'_id': int(id)}, {'$set': {'quality_format': quality}})

    async def get_quality_format(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('quality_format', 'keep')

    async def set_prefix(self, id, prefix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})

    async def get_prefix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('prefix', '')

    async def set_suffix(self, id, suffix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})

    async def get_suffix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('suffix', '')

    async def set_auto_clean(self, id, value):
        await self.col.update_one({'_id': int(id)}, {'$set': {'auto_clean': value}})

    async def get_auto_clean(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('auto_clean', True)

    async def get_all_rename_settings(self, id):
        user = await self.col.find_one({'_id': int(id)})
        if user:
            return {
                'rename_mode': user.get('rename_mode', 'manual'),
                'auto_detect_type': user.get('auto_detect_type', True),
                'auto_detect_language': user.get('auto_detect_language', True),
                'remove_words': user.get('remove_words', []),
                'replace_words': user.get('replace_words', {}),
                'quality_format': user.get('quality_format', 'keep'),
                'prefix': user.get('prefix', ''),
                'suffix': user.get('suffix', ''),
                'auto_clean': user.get('auto_clean', True)
            }
        return None


db = Database(Config.DB_URL, Config.DB_NAME)
