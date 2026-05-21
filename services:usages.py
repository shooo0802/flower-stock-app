from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime
from db import get_session
from models import Flower, Usage

def register_usage(project_id: str, flower_id: str, use_qty: float, reuse_qty: float) -> tuple[bool,str]:
    s = get_session()
    try:
        fl = s.get(Flower, flower_id)
        if not fl:
            return False, "花材IDが存在しません。"
        unit = fl.unit_price or 0.0
        cost = (use_qty or 0.0) * unit
        s.add(Usage(project_id=project_id, flower_id=flower_id, use_qty=use_qty or 0.0,
                    reuse_qty=reuse_qty or 0.0, unit_price=unit, cost=cost))
        # 即時反映（MVP）：used_qty += use − reuse
        delta = (use_qty or 0.0) - (reuse_qty or 0.0)
        fl.used_qty = max((fl.used_qty or 0.0) + delta, 0.0)
        fl.stock = max((fl.in_qty or 0.0) - (fl.used_qty or 0.0), 0.0)
        fl.state = "使用可" if fl.stock > 0 else "在庫なし"
        s.commit()
        return True, f"使用登録完了（案件:{project_id}, 花材:{flower_id}, 使用:{use_qty}, 再利用:{reuse_qty}）"
    except Exception as e:
        s.rollback()
        return False, f"エラー: {e}"
    finally:
        s.close()

def sync_usages_to_flowers() -> tuple[bool,str]:
    s = get_session()
    try:
        # flower_id ごとに Σuse − Σreuse
        rows = s.query(Usage.flower_id,
                       func.sum(Usage.use_qty).label("su"),
                       func.sum(Usage.reuse_qty).label("sr")).group_by(Usage.flower_id).all()
        m = {r[0]: (float(r[1] or 0.0) - float(r[2] or 0.0)) for r in rows}
        # 反映
        for fid, net_use in m.items():
            fl = s.get(Flower, fid)
            if not fl: continue
            fl.used_qty = max(net_use, 0.0)
            fl.stock = max((fl.in_qty or 0.0) - fl.used_qty, 0.0)
            fl.state = "使用可" if fl.stock > 0 else "在庫なし"
        s.commit()
        return True, "使用連携（Σ使用−Σ再利用）を完了しました。"
    except Exception as e:
        s.rollback()
        return False, f"エラー: {e}"
    finally:
        s.close()
