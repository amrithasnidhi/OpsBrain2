from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import datetime

from knowledge_graph.query import get_stale_claims
from knowledge_graph.graph import build_graph
from shared.schemas import StalenessRow

router = APIRouter(prefix="/api", tags=["dashboards"])

@router.get("/staleness")
def staleness():
    try:
        claims = get_stale_claims(staleness_days=0)  # get everything, compute status here
        rows = []
        today = datetime.date.today()
        
        for c in claims:
            # Simple heuristic for required_interval and last_inspection_date
            # The dummy data in the knowledge graph doesn't have these exact fields explicitly structured,
            # so we'll infer them from the claim and effective_date.
            interval_str = str(c.value) if c.value else "12 months"

            # Extract numbers from interval_str to approximate required interval in days
            # Default to 365 if not found
            import re
            nums = re.findall(r'\d+', interval_str)
            interval_days = int(nums[0]) * 30 if nums and "month" in interval_str.lower() else 365
            if nums and "year" in interval_str.lower():
                interval_days = int(nums[0]) * 365

            last_date = c.effective_date or (today - datetime.timedelta(days=365*2))
            
            # If effective_date is a string (e.g. from DB), parse it
            if isinstance(last_date, str):
                try:
                    last_date = datetime.date.fromisoformat(last_date)
                except ValueError:
                    last_date = (today - datetime.timedelta(days=365*2))

            days_passed = (today - last_date).days
            days_overdue = days_passed - interval_days
            
            status = "overdue" if days_overdue > 0 else ("warning" if days_overdue > -30 else "ok")
            
            rows.append(StalenessRow(
                equipment_tag=c.equipment_tag,
                required_interval=interval_str,
                last_inspection_date=last_date,
                days_overdue=days_overdue,
                status=status
            ))
            
        # Sort overdue first, then warning, then ok
        rows.sort(key=lambda r: (
            0 if r.status == 'overdue' else (1 if r.status == 'warning' else 2),
            -r.days_overdue
        ))
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph")
def get_graph_data():
    try:
        G = build_graph()
        nodes = []
        links = []
        
        for n, d in G.nodes(data=True):
            node_type = d.get("type", "unknown")
            color = "#3b82f6" if node_type == "equipment" else "#9ca3af" # blue for equipment, grey for doc
            nodes.append({
                "id": n,
                "label": d.get("name", n),
                "color": color,
                "group": node_type
            })
            
        for u, v, d in G.edges(data=True):
            edge_type = d.get("type", "")
            # Assuming conflicts are stored as 'conflict' or we check type
            color = "#ef4444" if edge_type.lower() == "conflict" else "#9ca3af" # red for conflicts, grey else
            links.append({
                "source": u,
                "target": v,
                "color": color,
                "label": edge_type
            })
            
        return {"nodes": nodes, "links": links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
