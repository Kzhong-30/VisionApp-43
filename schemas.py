from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class GarbageItemBase(BaseModel):
    name: str
    category: str
    disposal_method: str
    disposal_guide: str


class GarbageItemCreate(GarbageItemBase):
    pass


class GarbageItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    disposal_method: Optional[str] = None
    disposal_guide: Optional[str] = None


class GarbageItem(GarbageItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    points: int
    total_classifications: int
    correct_classifications: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithStats(User):
    accuracy: float


class ClassificationRecordBase(BaseModel):
    user_id: int
    item_name: str
    predicted_category: str
    actual_category: Optional[str] = None
    is_correct: bool = False
    points_earned: int = 0
    confidence: float = 0.0


class ClassificationRecordCreate(ClassificationRecordBase):
    pass


class ClassificationRecord(ClassificationRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClassifyResponse(BaseModel):
    item_name: str
    category: str
    confidence: float
    disposal_method: Optional[str] = None
    disposal_guide: Optional[str] = None


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    points: int
    total_classifications: int
    correct_classifications: int
    accuracy: float


class StatsResponse(BaseModel):
    total_users: int
    total_items: int
    total_classifications: int
    total_points: int
    avg_accuracy: float
    category_distribution: dict
