from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date
from db import get_session
from models import Flower, Lot, Purchase

def register_purchase(flower_id: str, lot_date: date, qty: float, amount: float) -> tuple[bool,str]:
    s = get_session()
    try:
        fl = s.get(Flower, flower_id)
        if not fl:
            return False, "花材IDが存在しません。先に花材を作成してください。"
        unit = (amount / qty) if qty and amount else 0.0
        # 仕入履歴
        s.add(Purchase(flower_id=flower_id, lot_date=lot_date, qty=qty, unit_price=unit, amount=amount))
        # ロット作成 or 既存ロット（同日ユニーク）に合算
        lot = s.scalar(select(Lot).where(Lot.flower_id==flower_id, Lot.lot_date==lot_date))
        if lot:
            # 同日ロットに合算（単価は移動平均でもよいが、ロット粒度を維持）
            total_qty = lot.qty + qty
            lot.unit_price = (lot.unit_price*lot.qty + unit*qty)/total_qty if total_qty>0 else lot.unit_price
            lot.qty += qty
            lot.remaining_qty += qty
        else:
            lot = Lot(flower_id=flower_id, lot_date=lot_date, unit_price=unit, qty=qty, remaining_qty=qty)
            s.add(lot)
        # 花材再計算
        from services.flowers import _recompute_flower_from_lots
        _recompute_flower_from_lots(s, fl)
        s.commit()
        return True, f"仕入登録完了（{flower_id}, {qty}本, 単価{unit:.2f}）"
    except Exception as e:
        s.rollback()
        return False, f"エラー: {e}"
    finally:
        s.close()
