from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db import get_session
from models import Project, Usage

def sync_projects_sum_and_remain() -> tuple[bool,str]:
    s = get_session()
    try:
        # project_id ごとに Σcost
        rows = s.query(Usage.project_id, func.sum(Usage.cost).label("sumc")).group_by(Usage.project_id).all()
        sum_map = {r[0]: float(r[1] or 0.0) for r in rows}
        projects = s.scalars(select(Project)).all()
        for p in projects:
            p.sum_cost = float(sum_map.get(p.id, 0.0))
            p.remain = float((p.budget or 0.0) - p.sum_cost)
        s.commit()
        return True, "Projects の使用原価合計と残予算を更新しました。"
    except Exception as e:
        s.rollback()
        return False, f"エラー: {e}"
    finally:
        s.close()
