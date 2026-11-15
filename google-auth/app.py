"""Đăng nhập / đăng ký bằng Google cho trang quản lý xiaozhi (minizjp).

Luồng: /auth/google/login -> Google -> /auth/google/callback
 -> tìm hoặc tạo sys_user (username = email Gmail) -> tạo token trong sys_user_token
 -> chuyển về /#/login?gtoken=... (trang login đã được sửa để nhận token này).
Chạy trong stack docker-compose_all.yml, Cloudflare route path /auth/* về service này.
"""
import os, time, secrets, hmac, hashlib, base64, logging
from urllib.parse import urlencode, quote
import bcrypt, httpx, pymysql
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse

CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
BASE = os.environ.get("PUBLIC_BASE", "https://xiaozhi.minizjp.com").rstrip("/")
REDIRECT_URI = BASE + "/auth/google/callback"
STATE_SECRET = (os.environ.get("STATE_SECRET") or CLIENT_SECRET).encode()
TOKEN_EXPIRE = 3600 * 12  # giống manager-api (SysUserTokenServiceImpl.EXPIRE)
DB = dict(host=os.environ.get("DB_HOST", "xiaozhi-esp32-server-db"), port=int(os.environ.get("DB_PORT", "3306")),
          user=os.environ.get("DB_USER", "root"), password=os.environ.get("DB_PASSWORD", "123456"),
          database=os.environ.get("DB_NAME", "xiaozhi_esp32_server"), charset="utf8mb4", autocommit=False)

log = logging.getLogger("google-auth")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def new_id() -> int:
    """ID kiểu snowflake (ms << 22 | ngẫu nhiên), vừa BIGINT như MyBatis-Plus ASSIGN_ID."""
    return (int(time.time() * 1000) << 22) | secrets.randbits(22)


def sign(value: str) -> str:
    return value + "." + hmac.new(STATE_SECRET, value.encode(), hashlib.sha256).hexdigest()[:32]


def unsign(signed: str):
    value, _, sig = (signed or "").rpartition(".")
    return value if value and hmac.compare_digest(sign(value), signed) else None


def back_to_login(**params):
    return RedirectResponse(BASE + "/#/login?" + urlencode(params), status_code=302)


def fail(msg: str):
    log.warning("login failed: %s", msg)
    resp = back_to_login(gerror=quote(msg))
    resp.delete_cookie("g_state", path="/auth")
    return resp


@app.get("/auth/health")
def health():
    return {"ok": True}


REMEMBER_DAYS = int(os.environ.get("REMEMBER_DAYS", "30"))


@app.get("/auth/google/login")
def google_login(remember: int = 1):
    state = secrets.token_urlsafe(24)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI, "response_type": "code",
        "scope": "openid email profile", "state": state, "prompt": "select_account"})
    resp = RedirectResponse(url, status_code=302)
    resp.set_cookie("g_state", sign(state + ":" + str(int(time.time())) + ":" + ("1" if remember else "0")), max_age=600,
                    httponly=True, secure=True, samesite="lax", path="/auth")
    return resp


@app.get("/auth/google/callback")
def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    if error:
        return fail("Đã huỷ đăng nhập Google")
    raw = unsign(request.cookies.get("g_state"))
    if not raw or not code or raw.split(":")[0] != state or time.time() - int(raw.split(":")[1]) > 600:
        return fail("Phiên đăng nhập Google hết hạn, vui lòng thử lại")
    remember = raw.split(":")[2:3] == ["1"]
    token_expire = REMEMBER_DAYS * 86400 if remember else TOKEN_EXPIRE
    try:
        with httpx.Client(timeout=15) as h:
            tok = h.post("https://oauth2.googleapis.com/token", data={
                "code": code, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI, "grant_type": "authorization_code"}).json()
            if "access_token" not in tok:
                return fail("Google từ chối: " + str(tok.get("error_description") or tok.get("error")))
            info = h.get("https://openidconnect.googleapis.com/v1/userinfo",
                         headers={"Authorization": "Bearer " + tok["access_token"]}).json()
    except Exception as e:
        return fail(f"Không kết nối được Google: {e}")

    email = (info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified"):
        return fail("Tài khoản Google chưa xác minh email")
    if len(email) > 50:
        return fail("Email quá dài (tối đa 50 ký tự)")

    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, status FROM sys_user WHERE username=%s", (email,))
            row = cur.fetchone()
            if row:
                user_id, status = row
                if status == 0:
                    return fail("Tài khoản đã bị khoá, liên hệ quản trị viên")
            else:
                # Đăng ký Google có công tắc riêng (GOOGLE_ALLOW_REGISTER), độc lập với đăng ký tên+mật khẩu
                if os.environ.get("GOOGLE_ALLOW_REGISTER", "true").lower() != "true":
                    return fail("Hệ thống đang tắt đăng ký tài khoản mới")
                user_id = new_id()
                pw = bcrypt.hashpw(secrets.token_urlsafe(32).encode(), bcrypt.gensalt(10)).decode()
                pw = "$2a$" + pw[4:]  # định dạng Spring BCrypt (người dùng Google không dùng mật khẩu này)
                cur.execute("INSERT INTO sys_user (id, username, password, super_admin, status, create_date, update_date) "
                            "VALUES (%s,%s,%s,0,1,NOW(),NOW())", (user_id, email, pw))
                log.info("tạo tài khoản Google mới: %s (%s)", email, user_id)
            token = secrets.token_hex(16)
            cur.execute("SELECT id FROM sys_user_token WHERE user_id=%s", (user_id,))
            if cur.fetchone():
                cur.execute("UPDATE sys_user_token SET token=%s, expire_date=DATE_ADD(NOW(), INTERVAL %s SECOND), "
                            "update_date=NOW() WHERE user_id=%s", (token, token_expire, user_id))
            else:
                cur.execute("INSERT INTO sys_user_token (id, user_id, token, expire_date, update_date, create_date) "
                            "VALUES (%s,%s,%s,DATE_ADD(NOW(), INTERVAL %s SECOND),NOW(),NOW())",
                            (new_id(), user_id, token, token_expire))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return fail(f"Lỗi máy chủ: {e}")
    finally:
        conn.close()

    log.info("đăng nhập Google: %s", email)
    resp = back_to_login(gtoken=token, gexp=token_expire)
    resp.delete_cookie("g_state", path="/auth")
    return resp


# ===================== Hạn sử dụng tài khoản (subscription) =====================
# Tài khoản thường: dùng thử TRIAL_DAYS ngày từ ngày tạo; admin cấp thêm 1/3/6/12 tháng.
# Server xiaozhi (patch receiveAudioHandle.py) đọc cùng bảng này để chặn robot khi hết hạn.
from fastapi import Header, HTTPException, Body
import datetime as _dt

TRIAL_DAYS = int(os.environ.get("TRIAL_DAYS", "3"))
PLANS = {1: "1 tháng", 3: "3 tháng", 6: "6 tháng", 12: "1 năm"}


def _db():
    return pymysql.connect(**DB)


def _ensure_table():
    conn = _db()
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS user_subscription (
                user_id BIGINT NOT NULL PRIMARY KEY,
                expire_at DATETIME NOT NULL,
                plan VARCHAR(30) NULL,
                updated_by BIGINT NULL,
                updated_at DATETIME NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def _startup():
    try:
        _ensure_table()
    except Exception as e:
        log.error("không tạo được bảng user_subscription: %s", e)


def _auth_user(authorization: str):
    """Xác thực bằng token của trang quản lý (header Authorization: Bearer <token> hoặc chỉ token)."""
    token = (authorization or "").replace("Bearer", "").strip()
    if not token:
        raise HTTPException(401, "Chưa đăng nhập")
    conn = _db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT u.id, u.super_admin, u.status FROM sys_user_token t JOIN sys_user u ON u.id = t.user_id "
                        "WHERE t.token = %s AND t.expire_date > NOW()", (token,))
            row = cur.fetchone()
    finally:
        conn.close()
    if not row or row[2] == 0:
        raise HTTPException(401, "Phiên đăng nhập hết hạn")
    return {"id": row[0], "super_admin": row[1] == 1}


def _status_rows(cur, user_ids=None):
    sql = ("SELECT u.id, u.username, u.super_admin, u.create_date, s.expire_at, s.plan, "
           "COALESCE(s.expire_at, DATE_ADD(u.create_date, INTERVAL %s DAY)) AS eff FROM sys_user u "
           "LEFT JOIN user_subscription s ON s.user_id = u.id")
    args = [TRIAL_DAYS]
    if user_ids:
        sql += " WHERE u.id IN (" + ",".join(["%s"] * len(user_ids)) + ")"
        args += list(user_ids)
    cur.execute(sql, args)
    now = _dt.datetime.now()
    out = {}
    for uid, username, sa, created, exp, plan, eff in cur.fetchall():
        unlimited = sa == 1
        days_left = None if unlimited else max(0, (eff - now).total_seconds() / 86400)
        out[str(uid)] = {
            "userid": str(uid), "username": username, "unlimited": unlimited,
            "expire_at": None if unlimited else eff.strftime("%Y-%m-%d %H:%M"),
            "expired": False if unlimited else eff < now,
            "days_left": None if unlimited else round(days_left, 1),
            "plan": "Admin" if unlimited else (plan or f"Dùng thử {TRIAL_DAYS} ngày"),
        }
    return out


@app.get("/auth/me/subscription")
def my_subscription(authorization: str = Header(None)):
    me = _auth_user(authorization)
    conn = _db()
    try:
        with conn.cursor() as cur:
            return {"code": 0, "data": _status_rows(cur, [me["id"]]).get(str(me["id"]))}
    finally:
        conn.close()


@app.get("/auth/admin/subscriptions")
def admin_subscriptions(ids: str = "", authorization: str = Header(None)):
    me = _auth_user(authorization)
    if not me["super_admin"]:
        raise HTTPException(403, "Chỉ admin")
    id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()][:500]
    conn = _db()
    try:
        with conn.cursor() as cur:
            return {"code": 0, "data": _status_rows(cur, id_list or None)}
    finally:
        conn.close()


@app.post("/auth/admin/subscriptions/extend")
def admin_extend(payload: dict = Body(...), authorization: str = Header(None)):
    """payload: {"userid": "...", "months": 1|3|6|12}  hoặc months=0 để thu hồi (hết hạn ngay)."""
    me = _auth_user(authorization)
    if not me["super_admin"]:
        raise HTTPException(403, "Chỉ admin")
    try:
        uid = int(str(payload.get("userid")))
        months = int(payload.get("months"))
    except Exception:
        raise HTTPException(400, "Thiếu userid/months")
    if months not in (0, *PLANS):
        raise HTTPException(400, "months phải là 0, 1, 3, 6 hoặc 12")
    conn = _db()
    try:
        with conn.cursor() as cur:
            rows = _status_rows(cur, [uid])
            if str(uid) not in rows:
                raise HTTPException(404, "Không tìm thấy người dùng")
            cur.execute("SELECT COALESCE(s.expire_at, DATE_ADD(u.create_date, INTERVAL %s DAY)) FROM sys_user u "
                        "LEFT JOIN user_subscription s ON s.user_id = u.id WHERE u.id = %s", (TRIAL_DAYS, uid))
            current = cur.fetchone()[0]
            now = _dt.datetime.now()
            if months == 0:
                new_exp, plan = now - _dt.timedelta(minutes=1), "Đã thu hồi"
            else:
                base = current if current and current > now else now  # cộng nối tiếp nếu còn hạn
                y, m = divmod(base.month - 1 + months, 12)
                import calendar
                day = min(base.day, calendar.monthrange(base.year + y, m + 1)[1])
                new_exp, plan = base.replace(year=base.year + y, month=m + 1, day=day), PLANS[months]
            cur.execute("INSERT INTO user_subscription (user_id, expire_at, plan, updated_by, updated_at) "
                        "VALUES (%s,%s,%s,%s,NOW()) ON DUPLICATE KEY UPDATE expire_at=VALUES(expire_at), "
                        "plan=VALUES(plan), updated_by=VALUES(updated_by), updated_at=NOW()",
                        (uid, new_exp, plan, me["id"]))
            conn.commit()
            log.info("admin %s cấp %s cho user %s -> hạn %s", me["id"], plan, uid, new_exp)
            return {"code": 0, "data": _status_rows(cur, [uid])[str(uid)]}
    finally:
        conn.close()



# ===================== Ghi nhớ đăng nhập =====================
@app.post("/auth/remember")
def remember_login(authorization: str = Header(None)):
    """Kéo dài token vừa đăng nhập (mật khẩu) lên REMEMBER_DAYS ngày khi người dùng tích "Ghi nhớ đăng nhập"."""
    token = (authorization or "").replace("Bearer", "").strip()
    if not token:
        raise HTTPException(401, "Chưa đăng nhập")
    conn = _db()
    try:
        with conn.cursor() as cur:
            n = cur.execute("UPDATE sys_user_token SET expire_date = DATE_ADD(NOW(), INTERVAL %s DAY), update_date = NOW() "
                            "WHERE token = %s AND expire_date > NOW()", (REMEMBER_DAYS, token))
        conn.commit()
    finally:
        conn.close()
    if not n:
        raise HTTPException(401, "Phiên đăng nhập hết hạn")
    return {"code": 0, "data": {"expire": REMEMBER_DAYS * 86400}}
