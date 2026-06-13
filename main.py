from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import engine, get_db, Base
from models import GarbageItem as GarbageItemModel, User as UserModel, ClassificationRecord as RecordModel
from schemas import (
    GarbageItemCreate, GarbageItemUpdate, GarbageItemResponse,
    ClassificationResponse, RecordCreate, RecordResponse,
    UserCreate, UserResponse, LeaderboardEntry, StatsResponse
)
from classifier import classify_image, DISPOSAL_GUIDES, DISPOSAL_METHODS

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="环保垃圾分类识别系统",
    description="基于 FastAPI + SQLite + Pillow 的智能垃圾分类识别应用",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def seed_data(db: Session):
    if db.query(GarbageItemModel).count() > 0:
        return

    seed_items = [
        GarbageItemModel(name="塑料瓶", category="可回收物", disposal_method="压扁后投放", disposal_guide="清空内容物，压扁后投入可回收物收集容器，瓶盖可单独回收"),
        GarbageItemModel(name="易拉罐", category="可回收物", disposal_method="压扁后投放", disposal_guide="倒空内容物，清洗后压扁投入可回收物收集容器"),
        GarbageItemModel(name="旧报纸", category="可回收物", disposal_method="捆扎后投放", disposal_guide="整理捆扎后投入可回收物收集容器，保持干燥清洁"),
        GarbageItemModel(name="纸箱", category="可回收物", disposal_method="拆叠后投放", disposal_guide="去除胶带和填充物，拆平折叠后投入可回收物收集容器"),
        GarbageItemModel(name="玻璃瓶", category="可回收物", disposal_method="清洗后投放", disposal_guide="倒空内容物并清洗，避免破碎，投入可回收物收集容器"),
        GarbageItemModel(name="旧衣服", category="可回收物", disposal_method="打包投放或捐赠", disposal_guide="清洗干净打包后投入可回收物收集容器或送至旧衣回收箱"),
        GarbageItemModel(name="金属餐具", category="可回收物", disposal_method="清洗后投放", disposal_guide="清洗后投入可回收物收集容器"),
        GarbageItemModel(name="塑料玩具", category="可回收物", disposal_method="清洗后投放", disposal_guide="拆除电池后清洗，投入可回收物收集容器"),
        GarbageItemModel(name="电池", category="有害垃圾", disposal_method="密封投放", disposal_guide="投入有害垃圾收集容器，请勿拆解，避免漏液污染"),
        GarbageItemModel(name="过期药品", category="有害垃圾", disposal_method="连同包装投放", disposal_guide="连同包装投入有害垃圾收集容器，建议送至药店回收点"),
        GarbageItemModel(name="荧光灯管", category="有害垃圾", disposal_method="包裹后投放", disposal_guide="用报纸或塑料袋包裹，避免破碎，投入有害垃圾收集容器"),
        GarbageItemModel(name="温度计", category="有害垃圾", disposal_method="密封投放", disposal_guide="用密封袋装好，投入有害垃圾收集容器"),
        GarbageItemModel(name="油漆桶", category="有害垃圾", disposal_method="密封后投放", disposal_guide="密封后投入有害垃圾收集容器，避免挥发"),
        GarbageItemModel(name="杀虫剂瓶", category="有害垃圾", disposal_method="排空后投放", disposal_guide="排空内容物，避免明火，投入有害垃圾收集容器"),
        GarbageItemModel(name="水银血压计", category="有害垃圾", disposal_method="密封投放", disposal_guide="用密封袋装好，投入有害垃圾收集容器"),
        GarbageItemModel(name="消毒剂瓶", category="有害垃圾", disposal_method="密封后投放", disposal_guide="密封后投入有害垃圾收集容器，避免挥发"),
        GarbageItemModel(name="剩菜剩饭", category="厨余垃圾", disposal_method="沥干后投放", disposal_guide="沥干水分，去除包装后投入厨余垃圾收集容器"),
        GarbageItemModel(name="果皮", category="厨余垃圾", disposal_method="直接投放", disposal_guide="直接投入厨余垃圾收集容器"),
        GarbageItemModel(name="蛋壳", category="厨余垃圾", disposal_method="直接投放", disposal_guide="直接投入厨余垃圾收集容器"),
        GarbageItemModel(name="茶叶渣", category="厨余垃圾", disposal_method="沥干后投放", disposal_guide="沥干水分后投入厨余垃圾收集容器"),
        GarbageItemModel(name="鱼骨", category="厨余垃圾", disposal_method="直接投放", disposal_guide="小骨头投入厨余垃圾收集容器，大骨头属于其他垃圾"),
        GarbageItemModel(name="菜叶", category="厨余垃圾", disposal_method="直接投放", disposal_guide="直接投入厨余垃圾收集容器"),
        GarbageItemModel(name="果核", category="厨余垃圾", disposal_method="直接投放", disposal_guide="直接投入厨余垃圾收集容器"),
        GarbageItemModel(name="咖啡渣", category="厨余垃圾", disposal_method="沥干后投放", disposal_guide="沥干水分后投入厨余垃圾收集容器"),
        GarbageItemModel(name="烟蒂", category="其他垃圾", disposal_method="熄灭后投放", disposal_guide="确认熄灭后投入其他垃圾收集容器"),
        GarbageItemModel(name="陶瓷碎片", category="其他垃圾", disposal_method="包裹后投放", disposal_guide="用报纸包裹防止割伤，投入其他垃圾收集容器"),
        GarbageItemModel(name="用过的纸巾", category="其他垃圾", disposal_method="直接投放", disposal_guide="投入其他垃圾收集容器"),
        GarbageItemModel(name="尿不湿", category="其他垃圾", disposal_method="直接投放", disposal_guide="投入其他垃圾收集容器"),
    ]
    db.add_all(seed_items)

    seed_users = [
        UserModel(username="环保达人", points=2680, total_classifications=320, correct_classifications=295),
        UserModel(username="绿色先锋", points=1950, total_classifications=240, correct_classifications=218),
        UserModel(username="分类小能手", points=1420, total_classifications=180, correct_classifications=160),
        UserModel(username="地球卫士", points=980, total_classifications=130, correct_classifications=110),
        UserModel(username="低碳生活家", points=650, total_classifications=90, correct_classifications=75),
    ]
    for idx, u in enumerate(seed_users):
        if u.correct_classifications > u.total_classifications:
            raise ValueError(
                f"种子用户 {u.username} 数据错误: correct_classifications({u.correct_classifications}) > total_classifications({u.total_classifications})"
            )
        if u.total_classifications < 0 or u.correct_classifications < 0:
            raise ValueError(
                f"种子用户 {u.username} 数据错误: 分类数不能为负数"
            )
    db.add_all(seed_users)
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
    return {
        "name": "环保垃圾分类识别系统",
        "version": "1.0.0",
        "docs": "/docs",
        "message": "欢迎使用智能垃圾分类识别 API，请访问 /docs 查看接口文档"
    }


@app.post("/classify", response_model=ClassificationResponse, tags=["图像识别"])
async def classify_garbage(
    file: UploadFile = File(..., description="垃圾图片文件"),
    db: Session = Depends(get_db)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="图片文件为空")
    category, confidence, item_name = classify_image(contents, file.filename or "")
    item = db.query(GarbageItemModel).filter(GarbageItemModel.name == item_name).first()
    if not item:
        item = db.query(GarbageItemModel).filter(GarbageItemModel.category == category).first()
    if item:
        return ClassificationResponse(
            item_name=item.name,
            category=item.category,
            confidence=confidence,
            disposal_method=item.disposal_method,
            disposal_guide=item.disposal_guide
        )
    method = DISPOSAL_METHODS.get(category, "直接投放")
    guide = DISPOSAL_GUIDES.get(category, "请按当地分类标准投放")
    return ClassificationResponse(
        item_name=item_name,
        category=category,
        confidence=confidence,
        disposal_method=method,
        disposal_guide=guide
    )

@app.get("/items", response_model=List[GarbageItemResponse], tags=["物品管理"])
def search_items(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: Session = Depends(get_db)
):
    query = db.query(GarbageItemModel)
    logger.info(f"搜索请求 - keyword: {repr(keyword)}, category: {repr(category)}")
    if keyword:
        query = query.filter(GarbageItemModel.name.contains(keyword))
        logger.info(f"应用关键词过滤: {repr(keyword)}")
    if category:
        valid_categories = ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"]
        if category not in valid_categories:
            raise HTTPException(status_code=400, detail=f"分类必须是以下之一: {valid_categories}")
        query = query.filter(GarbageItemModel.category == category)
    items = query.offset(skip).limit(limit).all()
    logger.info(f"查询到 {len(items)} 条结果")
    for item in items:
        logger.info(f"  - 物品: {item.name}, 分类: {item.category}")
    return items


@app.get("/items/{name}", response_model=GarbageItemResponse, tags=["物品管理"])
def get_item_by_name(name: str, db: Session = Depends(get_db)):
    item = db.query(GarbageItemModel).filter(GarbageItemModel.name == name).first()
    if not item:
        item = db.query(GarbageItemModel).filter(GarbageItemModel.name.contains(name)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"未找到物品: {name}")
    return item


@app.post("/items", response_model=GarbageItemResponse, tags=["管理后台"])
def create_item(item: GarbageItemCreate, db: Session = Depends(get_db)):
    valid_categories = ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"]
    if item.category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"分类必须是以下之一: {valid_categories}")
    existing = db.query(GarbageItemModel).filter(GarbageItemModel.name == item.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"物品已存在: {item.name}")
    db_item = GarbageItemModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/items/{item_id}", response_model=GarbageItemResponse, tags=["管理后台"])
def update_item(item_id: int, item_update: GarbageItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(GarbageItemModel).filter(GarbageItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail=f"未找到物品 ID: {item_id}")
    update_data = item_update.model_dump(exclude_unset=True)
    if "category" in update_data:
        valid_categories = ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"]
        if update_data["category"] not in valid_categories:
            raise HTTPException(status_code=400, detail=f"分类必须是以下之一: {valid_categories}")
    if "name" in update_data:
        existing = db.query(GarbageItemModel).filter(
            GarbageItemModel.name == update_data["name"],
            GarbageItemModel.id != item_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"物品名称已存在: {update_data['name']}")
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.post("/records", response_model=RecordResponse, tags=["积分系统"])
def create_record(record: RecordCreate, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"未找到用户 ID: {record.user_id}")
    is_correct = False
    points_earned = 0
    if record.actual_category:
        is_correct = record.predicted_category == record.actual_category
        points_earned = 10 if is_correct else 1
    db_record = RecordModel(
        user_id=record.user_id,
        item_name=record.item_name,
        predicted_category=record.predicted_category,
        actual_category=record.actual_category,
        is_correct=is_correct,
        points_earned=points_earned,
        confidence=record.confidence
    )
    db.add(db_record)
    user.points += points_earned
    user.total_classifications += 1
    if is_correct:
        user.correct_classifications += 1
    db.commit()
    db.refresh(db_record)
    return db_record

@app.get("/records", response_model=List[RecordResponse], tags=["积分系统"])
def get_records(
    user_id: Optional[int] = Query(None, description="用户 ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(RecordModel)
    if user_id:
        query = query.filter(RecordModel.user_id == user_id)
    return query.order_by(desc(RecordModel.created_at)).offset(skip).limit(limit).all()


@app.post("/users", response_model=UserResponse, tags=["用户管理"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"用户名已存在: {user.username}")
    db_user = UserModel(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    accuracy = (db_user.correct_classifications / db_user.total_classifications
                if db_user.total_classifications > 0 else 0.0)
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        points=db_user.points,
        total_classifications=db_user.total_classifications,
        correct_classifications=db_user.correct_classifications,
        accuracy_rate=round(accuracy, 4)
    )


@app.get("/users/{user_id}", response_model=UserResponse, tags=["用户管理"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"未找到用户 ID: {user_id}")
    accuracy = (user.correct_classifications / user.total_classifications
                if user.total_classifications > 0 else 0.0)
    return UserResponse(
        id=user.id,
        username=user.username,
        points=user.points,
        total_classifications=user.total_classifications,
        correct_classifications=user.correct_classifications,
        accuracy_rate=round(accuracy, 4)
    )

@app.get("/leaderboard", response_model=List[LeaderboardEntry], tags=["排行榜"])
def get_leaderboard(
    top: int = Query(10, ge=1, le=100, description="返回前 N 名"),
    db: Session = Depends(get_db)
):
    users = db.query(UserModel).order_by(desc(UserModel.points)).limit(top).all()
    result = []
    for rank, user in enumerate(users, 1):
        accuracy = (user.correct_classifications / user.total_classifications
                    if user.total_classifications > 0 else 0.0)
        result.append(LeaderboardEntry(
            rank=rank,
            user_id=user.id,
            username=user.username,
            points=user.points,
            correct_classifications=user.correct_classifications,
            accuracy_rate=round(accuracy, 4)
        ))
    return result


@app.get("/stats", response_model=StatsResponse, tags=["统计分析"])
def get_stats(db: Session = Depends(get_db)):
    categories = ["可回收物", "有害垃圾", "厨余垃圾", "其他垃圾"]
    category_counts = {}
    for cat in categories:
        count = db.query(RecordModel).filter(
            RecordModel.predicted_category == cat
        ).count()
        category_counts[cat] = count

    total_users = db.query(UserModel).count()
    total_classifications = db.query(RecordModel).count()
    correct_count = db.query(RecordModel).filter(
        RecordModel.is_correct == True
    ).count()
    total_actual = db.query(RecordModel).filter(
        RecordModel.actual_category.isnot(None)
    ).count()
    overall_accuracy = (correct_count / total_actual) if total_actual > 0 else 0.0

    weekly_trend = []
    for i in range(6, -1, -1):
        day = datetime.now().date() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day + timedelta(days=1), datetime.min.time())
        day_total = db.query(RecordModel).filter(
            RecordModel.created_at >= day_start,
            RecordModel.created_at < day_end
        ).count()
        day_correct = db.query(RecordModel).filter(
            RecordModel.created_at >= day_start,
            RecordModel.created_at < day_end,
            RecordModel.is_correct == True
        ).count()
        day_actual = db.query(RecordModel).filter(
            RecordModel.created_at >= day_start,
            RecordModel.created_at < day_end,
            RecordModel.actual_category.isnot(None)
        ).count()
        day_accuracy = (day_correct / day_actual) if day_actual > 0 else 0.0
        weekly_trend.append({
            "date": day.strftime("%Y-%m-%d"),
            "total": day_total,
            "correct": day_correct,
            "accuracy": round(day_accuracy, 4)
        })

    return StatsResponse(
        category_counts=category_counts,
        total_users=total_users,
        total_classifications=total_classifications,
        overall_accuracy=round(overall_accuracy, 4),
        weekly_trend=weekly_trend
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
