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

class GarbageItemResponse(GarbageItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: int
    username: str
    points: int
    total_classifications: int
    correct_classifications: int
    accuracy_rate: float
    class Config:
        from_attributes = True

class RecordCreate(BaseModel):
    user_id: int
    item_name: str
    predicted_category: str
    actual_category: Optional[str] = None
    confidence: float

class RecordResponse(BaseModel):
    id: int
    user_id: int
    item_name: str
    predicted_category: str
    actual_category: Optional[str] = None
    is_correct: bool
    points_earned: int
    confidence: float
    created_at: datetime
    class Config:
        from_attributes = True

class ClassificationResponse(BaseModel):
    item_name: str
    category: str
    confidence: float
    disposal_method: Optional[str] = None
    disposal_guide: Optional[str] = None

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    points: int
    correct_classifications: int
    accuracy_rate: float

class StatsResponse(BaseModel):
    category_counts: dict
    total_users: int
    total_classifications: int
    overall_accuracy: float
    weekly_trend: List[dict]
