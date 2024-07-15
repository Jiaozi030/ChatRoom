from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 数据库 URL
DATABASE_URL = "sqlite:///./chatroom.db"
metadata = MetaData()

# 使用 SQLAlchemy 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# 创建一个数据库会话类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 创建一个数据库基础类
Base = declarative_base()


# 创建 User 模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime)
    last_login = Column(DateTime)


# 创建 Message 模型
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, index=True)


# 创建所有表
Base.metadata.create_all(bind=engine)
