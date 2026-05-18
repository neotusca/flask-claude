from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import bcrypt
import sqlite3
import os

app = Flask(__name__)
# 실제 운영 환경에서는 환경변수로 관리: os.environ.get("SECRET_KEY")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

DB_PATH = "users.db"


# ──────────────────────────────────────────────
# DB 초기화 및 헬퍼 함수
# ──────────────────────────────────────────────

def get_db():
    """DB 커넥션 반환 (Row를 dict처럼 접근 가능하도록 설정)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    users 테이블 생성 및 초기 계정 삽입.
    앱 최초 실행 시 1회만 동작 (IF NOT EXISTS).
    """
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL,          -- bcrypt 해시
                role     TEXT    NOT NULL DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # 초기 계정이 없을 때만 삽입
        seed_users = [
            ("admin", "admin123", "admin"),
            ("user1", "password1", "user"),
        ]
        for username, raw_pw, role in seed_users:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()
            if not exists:
                hashed = bcrypt.hashpw(raw_pw.encode(), bcrypt.gensalt())
                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hashed.decode(), role),
                )
        conn.commit()


def get_user(username: str):
    """username으로 단일 유저 조회. 없으면 None 반환."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def verify_password(plain: str, hashed: str) -> bool:
    """입력 비밀번호와 DB의 bcrypt 해시를 비교."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ──────────────────────────────────────────────
# 데코레이터
# ──────────────────────────────────────────────

def login_required(f):
    """로그인하지 않은 사용자를 로그인 페이지로 리다이렉트"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            flash("로그인이 필요합니다.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────
# 라우트
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "username" in session else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("아이디와 비밀번호를 모두 입력해주세요.", "error")
            return render_template("login.html")

        user = get_user(username)  # DB 조회

        # ① 유저 존재 여부 + ② bcrypt 비밀번호 검증
        if user and verify_password(password, user["password"]):
            session["username"] = user["username"]
            session["role"]     = user["role"]
            flash(f"환영합니다, {user['username']}님!", "success")
            return redirect(url_for("dashboard"))
        else:
            # 존재하지 않는 ID / 비밀번호 불일치 → 동일 메시지로 응답 (사용자 열거 방지)
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session.get("role", "user"),
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("로그아웃 되었습니다.", "info")
    return redirect(url_for("login"))


# ──────────────────────────────────────────────
# 앱 시작
# ──────────────────────────────────────────────

if __name__ == "__main__":
    init_db()   # 테이블 생성 + 초기 계정 삽입
    app.run(debug=True, port=5000)
