from pathlib import Path

path = Path("src/api/main.py")
content = path.read_text(encoding="utf-8")

import_line = "from src.api.routers.pros_cons import router as pros_cons_router"

if import_line not in content:
    anchor = "from src.api.routers.portfolio import router as portfolio_router"
    content = content.replace(anchor, anchor + "\n" + import_line)

register_line = "app.include_router(pros_cons_router)"

if register_line not in content:
    anchor = "app.include_router(portfolio_router)"
    content = content.replace(anchor, anchor + "\n" + register_line)

path.write_text(content, encoding="utf-8")
print("Pros & Cons router registered.")
