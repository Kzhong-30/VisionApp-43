from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class GarbageItem(Base):
    __tablename__ = "garbage_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    disposal_method = Column(String, nullable=False)
    disposal_guide = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    points = Column(Integer, default=0)
    total_classifications = Column(Integer, default=0)
    correct_classifications = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    records = relationship("ClassificationRecord", back_populates="user")


class ClassificationRecord(Base):
    __tablename__ = "classification_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_name = Column(String, nullable=False)
    predicted_category = Column(String, nullable=False)
    actual_category = Column(String, nullable=True)
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="records")
