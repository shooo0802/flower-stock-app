import pandas as pd
from sqlalchemy import select
from db import get_session
from models import Project, Flower, Usage

def dashboard_frames():
    s = get_session()
    try:
        # Projects（撮影日順）
        projs = s.scalars(select(Project)).all()
        df_proj = pd.DataFrame([{
            "案件ID": p.id, "クライアント名": p.client_name,
            "撮影日": p.shoot_date.isoformat() if p.shoot_date else "",
            "テーマ": p.theme, "色味": p.tone, "予算": p.budget,
            "使用原価合計": p.sum_cost, "残予算": p.remain
        } for p in projs])
        if not df_proj.empty:
            df_proj = df_proj.sort_values("撮影日", na_position="last")

        # Flowers（在庫>0）
        flows = s.scalars(select(Flower)).all()
        df_flow = pd.DataFrame([{
            "花材ID": f.id, "花材名": f.name, "色": f.color,
            "入荷数量": f.in_qty, "使用数量": f.used_qty, "在庫": f.stock
        } for f in flows])
        if not df_flow.empty:
            df_flow = df_flow[df_flow["在庫"] > 0]

        # Usages（案件ID／クライアント／花材名／数量／原価）
        uses = s.query(Usage, Project).join(Project, Usage.project_id==Project.id, isouter=True).all()
        df_use = pd.DataFrame([{
            "案件ID": u.project_id, "クライアント名": (p.client_name if p else ""),
            "花材名": (s2.name if (s2:=s.get(Flower, u.flower_id)) else u.flower_id),
            "使用数量": u.use_qty, "使用原価": u.cost
        } for u,p in uses])

        return df_proj, df_flow, df_use
    finally:
        s.close()
