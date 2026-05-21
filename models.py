from sqlalchemy import Column, Integer, Float, String, Date, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime

class Flower(Base):
    __tablename__ = "flowers"
    id = Column(String, primary_key=True)  # 花材ID
    name = Column(String, index=True)
    color = Column(String, index=True)
    unit_price = Column(Float, default=0.0)   # 代表単価（残在庫加重平均）
    in_qty = Column(Float, default=0.0)       # 入荷数量合計（lots.remaining の合計）
    used_qty = Column(Float, default=0.0)     # 使用数量合計（使用連携）
    stock = Column(Float, default=0.0)        # 在庫 = in_qty - used_qty
    state = Column(String, default="在庫なし")

    lots = relationship("Lot", back_populates="flower")

class Lot(Base):
    __tablename__ = "lots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    flower_id = Column(String, ForeignKey("flowers.id"), index=True)
    lot_date = Column(Date, index=True)
    unit_price = Column(Float, default=0.0)
    qty = Column(Float, default=0.0)            # 仕入時数量
    remaining_qty = Column(Float, default=0.0)  # 仕入−廃棄（FIFO消化対象）

    flower = relationship("Flower", back_populates="lots")
    __table_args__ = (UniqueConstraint("flower_id", "lot_date", name="uq_lot_per_day"),)

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    flower_id = Column(String, index=True)
    lot_date = Column(Date, index=True)
    qty = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Usage(Base):
    __tablename__ = "usages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, index=True)
    flower_id = Column(String, index=True)
    use_qty = Column(Float, default=0.0)
    reuse_qty = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True)   # 案件ID
    client_name = Column(String, index=True)
    shoot_date = Column(Date)
    theme = Column(String)
    tone = Column(String)
    budget = Column(Float, default=0.0)
    sum_cost = Column(Float, default=0.0)
    remain = Column(Float, default=0.0)

class WasteLog(Base):
    __tablename__ = "waste_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    flower_id = Column(String, index=True)
    flower_name = Column(String)
    color = Column(String)
    lot_date = Column(Date)
    waste_qty = Column(Float, default=0.0)
    stock_after = Column(Float, default=0.0)
    actor = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String)
    event = Column(String)
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
