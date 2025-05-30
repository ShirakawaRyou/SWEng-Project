# backend/utils/db.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie

from backend.config import settings
from backend.models.user import User # 导入 User Document 模型
from backend.models.resume import Resume # 导入 Resume Document 模型
from backend.models.processed_jd import ProcessedJD # 导入 ProcessedJD Document 模型

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

# 创建数据库实例
db_manager = MongoDB()

# 连接到 MongoDB
async def connect_to_mongo():
    print("Attempting to connect to MongoDB...")
    try:
        # Atlas连接字符串通常包含 retryWrites=true&w=majority，确保使用了支持这些的驱动版本
        # MotorClient 可以直接使用 Atlas SRV 连接字符串
        db_manager.client = AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING + "&connectTimeoutMS=30000")
        # 在init_beanie中指定数据库，而不是在这里获取特定数据库名称的实例
        # db_manager.db = db_manager.client[settings.MONGO_DATABASE_NAME] # 这行可以移到init_beanie之后或省略
        
        # 验证连接 (可选，但推荐)
        # await db_manager.client.admin.command('ping') # Motor本身不直接提供admin属性，需要获取database实例
        # 获取默认数据库或配置文件中的数据库来执行ping
        admin_db = db_manager.client.admin # 或者 settings.MONGO_DATABASE_NAME
        await admin_db.command('ping')

        print(f"Successfully connected to MongoDB server. Target database for Beanie: '{settings.MONGO_DATABASE_NAME}'")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

# 关闭 MongoDB 连接
async def close_mongo_connection():
    if db_manager.client:
        print("Closing MongoDB connection...")
        db_manager.client.close()
        print("MongoDB connection closed.")

# 初始化数据库    
async def initialize_database():
    """初始化Beanie，注册Document模型，并创建索引"""
    if not db_manager.client:
        # 确保在调用 Beanie 初始化之前，MongoDB 客户端已连接
        # connect_to_mongo 应该在应用启动时先被调用
        raise Exception("MongoDB client not initialized. Call connect_to_mongo first.")
    
    # 获取在 settings 中配置的数据库实例
    database_instance = db_manager.client[settings.MONGO_DATABASE_NAME]

    print(f"Initializing Beanie with database: '{database_instance.name}'")
    await init_beanie(
        database=database_instance, # 使用正确的数据库实例
        document_models=[
            User,
            Resume,
            ProcessedJD,  # 添加 ProcessedJD 模型
            # 如果有更多Document模型，在这里添加
        ]
    )
    print("Beanie initialized successfully. Collections and indexes should be created/updated if defined in models.")

def get_database() -> AsyncIOMotorDatabase:
    """获取原始的Motor数据库实例（如果需要直接操作，不通过Beanie）"""
    if db_manager.client is None:
        raise Exception("Database client not initialized.")
    return db_manager.client[settings.MONGO_DATABASE_NAME]

# 注意：Beanie 初始化后，你可以直接从模型类进行数据库操作，例如 User.find_one(...)