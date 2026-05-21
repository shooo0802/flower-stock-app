from sqlalchemy import select, asc, func
from sqlalchemy.orm import Session
from datetime import date, datetime
from db import get_session
from models import Flower, Lot, WasteLog
from typing import Tuple, List

def _recompute_flower_from_lots(s: Session, flower: Flower):
    """lots から in_qty, unit_price（残在庫加重平均）, stock/state を再計算して保存"""
    lots = s.scalars(select(Lot).where(Lot.flower_id==flower.id)).all()
    in_qty = sum(l.remaining_qty for l in lots)
    # 残在庫のみで加重平均
    alive = [l for l in lots if l.remaining_qty > 0]
    total_v = sum(l.unit_price * l.remaining_qty for l in alive)
    total_q = sum(l.remaining_qty for l in alive)
    unit = (total_v / total_q) if total_q > 0 else 0.0
    flower.in_qty = in_qty
    flower.unit_price = unit
    flower.stock = max(flower.in_qty - flower.used_qty, 0.0)
    flower.state = "使用可" if flower.stock > 0 else "在庫なし"

def fifo_waste(flower_id: str, waste_qty: float, actor: str = "") -> Tuple[bool, str]:
    """古いlotから remaining_qty を削る。Flowerを再計算。WasteLog追加。"""
    s = get_session()
    try:
        if waste_qty is None or waste_qty <= 0:
            return False, "廃棄数量は1以上で入力してください。"
        flower = s.get(Flower, flower_id)
        if not flower:
            return False, "花材IDが見つかりません。"

        lots = s.scalars(select(Lot).where(Lot.flower_id==flower_id).order_by(asc(Lot.lot_date))).all()
        remaining = float(waste_qty)
        for lot in lots:
            if remaining <= 0: break
            stock_lot = max(lot.remaining_qty, 0.0)
            if stock_lot <= 0: continue
            take = min(stock_lot, remaining)
            lot.remaining_qty = stock_lot - take
            # WasteLog
            wl = WasteLog(
                flower_id=flower.id, flower_name=flower.name, color=flower.color,
                lot_date=lot.lot_date, waste_qty=take, stock_after=max(lot.remaining_qty - 0.0, 0.0),
                actor=actor or ""
            )
            s.add(wl)
            remaining -= take

        if remaining > 0:
            # 在庫不足だが、ここまでの消化は有効
            warn = f"在庫不足につき {remaining} 本は廃棄できませんでした。"
        else:
            warn = None

        _recompute_flower_from_lots(s, flower)
        s.commit()
        msg = "FIFO廃棄を完了。代表単価を残在庫加重平均で再計算しました。"
        if warn: msg += f"（注意: {warn}）"
        return True, msg
    except Exception as e:
        s.rollback()
        return False, f"エラー: {e}"
    finally:
        s.close()
