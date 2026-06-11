from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from typing import Optional, List

from database import engine, get_db, Base
from models import GarbageItem, User, ClassificationRecord
from schemas import (
    GarbageItemCreate, GarbageItemUpdate, GarbageItem as GarbageItemSchema,
    UserCreate, User as UserSchema, UserWithStats,
    ClassificationRecordCreate, ClassificationRecord as ClassificationRecordSchema,
    ClassifyResponse, LeaderboardEntry, StatsResponse,
)
from classifier import classify_image, CATEGORIES, DISPOSAL_GUIDES, DISPOSAL_METHODS

Base.metadata.create_all(bind=engine)

app = FastAPI(title="垃圾分类识别系统", description="基于图像识别的智能垃圾分类API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def seed_data(db: Session):
    import random
    items_data = [
        ("塑料瓶", "可回收物"), ("易拉罐", "可回收物"), ("旧报纸", "可回收物"), ("纸箱", "可回收物"),
        ("玻璃瓶", "可回收物"), ("旧衣服", "可回收物"), ("金属餐具", "可回收物"), ("塑料玩具", "可回收物"),
        ("电池", "有害垃圾"), ("过期药品", "有害垃圾"), ("荧光灯管", "有害垃圾"), ("温度计", "有害垃圾"),
        ("油漆桶", "有害垃圾"), ("杀虫剂瓶", "有害垃圾"), ("水银血压计", "有害垃圾"), ("消毒剂瓶", "有害垃圾"),
        ("剩菜剩饭", "厨余垃圾"), ("果皮", "厨余垃圾"), ("蛋壳", "厨余垃圾"), ("茶叶渣", "厨余垃圾"),
        ("鱼骨", "厨余垃圾"), ("菜叶", "厨余垃圾"), ("果皮核", "厨余垃圾"), ("咖啡渣", "厨余垃圾"),
        ("烟蒂", "其他垃圾"), ("陶瓷碎片", "其他垃圾"), ("用过的纸巾", "其他垃圾"), ("尿不湿", "其他垃圾"),
    ]

    existing_count = db.query(GarbageItem).count()
    if existing_count == 0:
        for name, category in items_data:
            item = GarbageItem(
                name=name,
                category=category,
                disposal_method=DISPOSAL_METHODS[category],
                disposal_guide=DISPOSAL_GUIDES[category],
            )
            db.add(item)
        db.commit()

    users_data = ["小明", "小红", "小刚", "小美", "小强"]
    existing_users = db.query(User).count()
    if existing_users == 0:
        for username in users_data:
            user = User(
                username=username,
                points=random.randint(50, 500),
                total_classifications=random.randint(10, 100),
                correct_classifications=random.randint(5, 90),
            )
            db.add(user)
        db.commit()


@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        seed_data(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "垃圾分类识别系统 API", "version": "1.0.0"}


@app.post("/classify", response_model=ClassifyResponse)
async def classify_image_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_bytes = await file.read()
    category, confidence, item_name = classify_image(image_bytes, file.filename)

    item = db.query(GarbageItem).filter(GarbageItem.name == item_name).first()
    disposal_method = item.disposal_method if item else DISPOSAL_METHODS.get(category, "")
    disposal_guide = item.disposal_guide if item else DISPOSAL_GUIDES.get(category, "")

    return ClassifyResponse(
        item_name=item_name,
        category=category,
        confidence=confidence,
        disposal_method=disposal_method,
        disposal_guide=disposal_guide,
    )


@app.get("/items", response_model=List[GarbageItemSchema])
def get_items(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(GarbageItem)
    if keyword:
        query = query.filter(GarbageItem.name.contains(keyword))
    if category:
        query = query.filter(GarbageItem.category == category)
    return query.offset(skip).limit(limit).all()


@app.get("/items/{name}", response_model=GarbageItemSchema)
def get_item_by_name(name: str, db: Session = Depends(get_db)):
    item = db.query(GarbageItem).filter(GarbageItem.name == name).first()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    return item


@app.post("/items", response_model=GarbageItemSchema)
def create_item(item: GarbageItemCreate, db: Session = Depends(get_db)):
    existing = db.query(GarbageItem).filter(GarbageItem.name == item.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="物品已存在")
    db_item = GarbageItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.put("/items/{item_id}", response_model=GarbageItemSchema)
def update_item(item_id: int, item_update: GarbageItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(GarbageItem).filter(GarbageItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="物品不存在")
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.post("/records", response_model=ClassificationRecordSchema)
def create_record(record: ClassificationRecordCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db_record = ClassificationRecord(**record.dict())
    db.add(db_record)

    user.total_classifications += 1
    if record.is_correct:
        user.correct_classifications += 1
        user.points += record.points_earned

    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/records", response_model=List[ClassificationRecordSchema])
def get_records(
    user_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(ClassificationRecord)
    if user_id:
        query = query.filter(ClassificationRecord.user_id == user_id)
    return query.order_by(ClassificationRecord.created_at.desc()).offset(skip).limit(limit).all()


@app.post("/users", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=UserWithStats)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    accuracy = (user.correct_classifications / user.total_classifications * 100) if user.total_classifications > 0 else 0.0
    return UserWithStats(
        id=user.id,
        username=user.username,
        points=user.points,
        total_classifications=user.total_classifications,
        correct_classifications=user.correct_classifications,
        created_at=user.created_at,
        accuracy=round(accuracy, 2),
    )


@app.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.points.desc()).limit(limit).all()
    result = []
    for rank, user in enumerate(users, start=1):
        accuracy = (user.correct_classifications / user.total_classifications * 100) if user.total_classifications > 0 else 0.0
        result.append(LeaderboardEntry(
            rank=rank,
            username=user.username,
            points=user.points,
            total_classifications=user.total_classifications,
            correct_classifications=user.correct_classifications,
            accuracy=round(accuracy, 2),
        ))
    return result


@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_items = db.query(GarbageItem).count()
    total_records = db.query(ClassificationRecord).count()
    total_points = db.query(sa_func.sum(User.points)).scalar() or 0

    users = db.query(User).all()
    total_correct = sum(u.correct_classifications for u in users)
    total_class = sum(u.total_classifications for u in users)
    avg_accuracy = (total_correct / total_class * 100) if total_class > 0 else 0.0

    category_dist = {}
    for cat in CATEGORIES.keys():
        count = db.query(GarbageItem).filter(GarbageItem.category == cat).count()
        category_dist[cat] = count

    return StatsResponse(
        total_users=total_users,
        total_items=total_items,
        total_classifications=total_records,
        total_points=total_points,
        avg_accuracy=round(avg_accuracy, 2),
        category_distribution=category_dist,
    )
