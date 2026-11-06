import os, re
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from dotenv import load_dotenv
from .db import connect, init_db

load_dotenv()

app = FastAPI(title="CloudHost")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-key-change-me"),
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
init_db()


def user_for(req):
    uid = req.session.get("uid")
    if not uid:
        return None
    with connect() as db:
        return db.execute(
            "SELECT id,email FROM users WHERE id=?", (uid,)
        ).fetchone()


def render(req, template, **kw):
    return templates.TemplateResponse(
        template, {"request": req, **kw}
    )


@app.get("/")
def dashboard(req: Request):
    u = user_for(req)
    if not u:
        return RedirectResponse("/login", 303)

    with connect() as db:
        ps = db.execute(
            "SELECT * FROM projects WHERE user_id=? ORDER BY id DESC",
            (u["id"],)
        ).fetchall()

    return render(
        req, "dashboard.html",
        user=u,
        projects=ps,
        total=len(ps),
        running=sum(x["status"] == "Running" for x in ps)
    )


@app.get("/signup")
def signup_page(req: Request):
    return render(req, "auth.html", mode="signup", error=None)


@app.post("/signup")
def signup(req: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(password) < 10:
        return render(
            req, "auth.html",
            mode="signup",
            error="Enter a valid email and password of at least 10 characters."
        )

    with connect() as db:
        try:
            cur = db.execute(
                "INSERT INTO users(email,password_hash) VALUES(?,?)",
                (email, pwd.hash(password))
            )
            req.session["uid"] = cur.lastrowid
        except Exception:
            return render(
                req, "auth.html",
                mode="signup",
                error="Email already registered."
            )

    return RedirectResponse("/", 303)


@app.get("/login")
def login_page(req: Request):
    return render(req, "auth.html", mode="login", error=None)


@app.post("/login")
def login(req: Request, email: str = Form(...), password: str = Form(...)):
    with connect() as db:
        u = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email.strip().lower(),)
        ).fetchone()

    if not u or not pwd.verify(password, u["password_hash"]):
        return render(
            req, "auth.html",
            mode="login",
            error="Email or password incorrect."
        )

    req.session.clear()
    req.session["uid"] = u["id"]
    return RedirectResponse("/", 303)


@app.post("/logout")
def logout(req: Request):
    req.session.clear()
    return RedirectResponse("/login", 303)


@app.post("/projects")
def create(req: Request, name: str = Form(...), runtime: str = Form(...)):
    u = user_for(req)
    if not u:
        return RedirectResponse("/login", 303)

    name = name.strip()

    if not name or len(name) > 40 or runtime not in ("python", "node"):
        raise HTTPException(400, "Invalid project")

    with connect() as db:
        if db.execute(
            "SELECT COUNT(*) FROM projects WHERE user_id=?",
            (u["id"],)
        ).fetchone()[0] >= 5:
            raise HTTPException(400, "Starter limit: 5 projects")

        db.execute(
            "INSERT INTO projects(user_id,name,runtime) VALUES(?,?,?)",
            (u["id"], name, runtime)
        )

    return RedirectResponse("/", 303)


@app.post("/projects/{pid}/delete")
def delete(req: Request, pid: int):
    u = user_for(req)
    if not u:
        return RedirectResponse("/login", 303)

    with connect() as db:
        db.execute(
            "DELETE FROM projects WHERE id=? AND user_id=?",
            (pid, u["id"])
        )

    return RedirectResponse("/", 303)


@app.get("/health")
def health():
    return {"status": "ok"}
