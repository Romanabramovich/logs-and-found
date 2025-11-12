from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Log(Base):
    __tablename__ = 'logs'
    id = Column(BigInteger, primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    level = Column(String(10), nullable=False)
    source = Column(String(100), nullable=False)
    application = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    log_metadata = Column('metadata', JSONB)  # Maps to 'metadata' column in database  
    created_at = Column(DateTime(timezone=True), server_default='NOW()')  
