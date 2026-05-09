"""
Meteo Dashboard — навчальний frontend для Уроку 31: HTTP & REST API

Цей Streamlit-додаток Є клієнтом:
  - він робить HTTP-запити до FastAPI (сервера)
  - через бібліотеку requests
  - отримує JSON у відповідь
  - відображає дані через pandas + plotly

Запуск:
  docker compose up --build
  Потім відкрий: http://localhost:8501
"""
import os
import json
import time
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# КОНФІГУРАЦІЯ
# ─────────────────────────────────────────────────────────────────────────
# API_URL — де знаходиться FastAPI backend?
#
#   В Docker (через docker-compose):
#       app_fastapi:8000  ← ім'я сервісу з docker-compose.yaml
#       Streamlit → FastAPI йде через внутрішню Docker-мережу
#
#   Локально (без Docker):
#       localhost:8000
#
#   Через ngrok (публічний доступ):
#       https://xxxx.ngrok-free.app
# ═══════════════════════════════════════════════════════════════════════════
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Метеостанції України: назва → WMO код станції
STATIONS_UA: dict[str, str] = {
    "Київ":          "33345",
    "Харків":        "34300",
    "Дніпро":        "34504",
    "Львів":         "33393",
    "Полтава":       "33506",
    "Одеса":         "33837",
    "Чернігів":      "33135",
    "Суми":          "33275",
    "Рівне":         "33301",
    "Житомир":       "33325",
    "Тернопіль":     "33415",
    "Хмельницький":  "33429",
}

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Meteo Dashboard | Урок 31",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# HELPER: make_request()
#
# Навчальна обгортка навколо requests — зберігає ВСІ деталі HTTP-обміну:
# - заголовки запиту/відповіді
# - тіло запиту
# - статус-код
# - час відповіді
# ═══════════════════════════════════════════════════════════════════════════
def make_request(method: str, url: str, **kwargs) -> dict:
    """
    Виконує HTTP-запит та повертає словник з повними деталями.
    Використовується в HTTP Inspector для навчальних цілей.
    """
    result = {
        "url": url,
        "method": method.upper(),
        "request_headers": {},
        "request_body": None,
        "status_code": None,
        "response_headers": {},
        "response_body": None,
        "elapsed_ms": None,
        "error": None,
    }

    try:
        # Головний HTTP-запит — тут Python блокується і чекає відповіді
        t0 = time.monotonic()
        response = requests.request(
            method,
            url,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=(5.0, 60.0),   # (connect timeout, read timeout) — ЗАВЖДИ встановлюй!
            **kwargs,
        )
        elapsed = (time.monotonic() - t0) * 1000

        # Зберігаємо деталі ЗАПИТУ (PreparedRequest — точні байти, що пішли по дроту)
        result["request_headers"] = dict(response.request.headers)
        result["request_body"] = response.request.body

        # Зберігаємо деталі ВІДПОВІДІ
        result["status_code"] = response.status_code
        result["response_headers"] = dict(response.headers)
        result["elapsed_ms"] = round(elapsed, 1)

        try:
            result["response_body"] = response.json()
        except Exception:
            result["response_body"] = response.text

    except requests.exceptions.ConnectionError as e:
        result["error"] = f"ConnectionError: не вдалося з'єднатись\n\n{e}"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout: сервер не відповів за 60 секунд"
    except requests.exceptions.RequestException as e:
        result["error"] = f"RequestException: {e}"

    return result


def show_status(result: dict):
    """Відображає статус-код з кольором та час."""
    if result["error"]:
        st.error(f"❌ {result['error']}")
        return False

    code = result["status_code"]
    ms = result["elapsed_ms"]

    if 200 <= code < 300:
        st.success(f"✅ HTTP {code} | ⏱️ {ms} ms")
    elif 400 <= code < 500:
        st.error(f"❌ HTTP {code} | ⏱️ {ms} ms")
    elif 500 <= code < 600:
        st.error(f"🔥 HTTP {code} Server Error | ⏱️ {ms} ms")
    else:
        st.warning(f"⚠️ HTTP {code} | ⏱️ {ms} ms")

    return 200 <= code < 300


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ Налаштування")

    # Дозволяємо студентам змінити API URL (напр. на ngrok)
    st.markdown("**API URL** _(backend адреса)_:")
    api_url = st.text_input(
        label="api_url",
        value=API_URL,
        label_visibility="collapsed",
        placeholder="http://localhost:8000",
    )

    # Health-check кнопка
    if st.button("🔍 Перевірити з'єднання", use_container_width=True):
        r = make_request("GET", f"{api_url}/docs")
        if r["status_code"] == 200:
            st.success(f"✅ API доступний  ({r['elapsed_ms']} ms)")
        elif r["error"]:
            st.error(r["error"])
        else:
            st.warning(f"HTTP {r['status_code']}")

    st.divider()

    st.markdown("**Країна:**")
    country = st.selectbox("country", ["ua", "bel"], label_visibility="collapsed")

    st.markdown("**Станція:**")
    station_name = st.selectbox(
        "station", list(STATIONS_UA.keys()), label_visibility="collapsed"
    )
    station_id = STATIONS_UA[station_name]
    st.caption(f"WMO код: `{station_id}`")

    st.divider()

    st.markdown("**Фільтр по даті:**")
    use_date = st.checkbox("Фільтрувати по даті")
    selected_date = None
    if use_date:
        selected_date = st.date_input("date", value=datetime.now().date(),
                                       label_visibility="collapsed")

    st.markdown("**Поля у відповіді:**")
    all_fields = [
        "year", "month", "day", "hour",
        "temperature", "pressure", "sea_level_pressure",
        "wind_speed", "wind_dir", "relative_humidity",
        "dew_point_temperature",
    ]
    selected_fields = st.multiselect(
        "fields",
        all_fields,
        default=["year", "month", "day", "hour", "temperature", "pressure"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown(f"**Swagger UI:**")
    st.markdown(f"[{api_url}/docs]({api_url}/docs)")
    st.caption("Інтерактивна документація FastAPI")


# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════
st.title("🌦️ Meteo Dashboard")
st.markdown("**Урок 31 — HTTP & REST API | Streamlit ↔ FastAPI ↔ MongoDB**")

with st.expander("📐 Архітектура: як це працює", expanded=False):
    st.code(
        """
┌───────────────────────────────────────────────────────────────────┐
│   КЛІЄНТ: Streamlit (цей додаток, порт 8501)                      │
│                                                                    │
│   import requests                                                  │
│                                                                    │
│   response = requests.post(                                        │
│       "http://app_fastapi:8000/filter_telegrams/",                 │
│       json={"country_code": "ua", "station_id": "33345"},         │
│       headers={"Content-Type": "application/json"},               │
│       timeout=(5.0, 60.0),   # ← ЗАВЖДИ!                          │
│   )                                                                │
│   data = response.json()["results"]  # ← десеріалізація JSON      │
└───────────────────────────┬───────────────────────────────────────┘
                            │  HTTP POST  (JSON body)
                            │  TCP через Docker network
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│   СЕРВЕР: FastAPI (порт 8000)                                      │
│                                                                    │
│   @app.post("/filter_telegrams/")                                  │
│   def filter_telegrams(filter: TelegramFilter):                   │
│       results = db["ua"].find(query)                               │
│       return {"results": [...]}   # ← JSON відповідь              │
└───────────────────────────┬───────────────────────────────────────┘
                            │  PyMongo query
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│   DATABASE: MongoDB (порт 27017)                                   │
│                                                                    │
│   Collection "ua":                                                 │
│   { "id_telegram": "33345...", "data": {"temperature": 22.5, ...}}│
└───────────────────────────────────────────────────────────────────┘
                            │  JSON documents
                            ▼
              pandas DataFrame  →  Plotly chart
        """,
        language="text",
    )

# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════
tab_data, tab_download, tab_crud, tab_inspector, tab_guide = st.tabs([
    "📊 Дані та Графік",
    "⬇️ Завантажити з Ogimet",
    "✏️ CRUD операції",
    "🔬 HTTP Inspector",
    "📚 API Guide",
])

# ───────────────────────────────────────────────────────────────────────────
# TAB 1: Дані та Графік — POST /filter_telegrams/
# ───────────────────────────────────────────────────────────────────────────
with tab_data:
    st.subheader("POST /filter_telegrams/")
    st.markdown(
        "Запит повертає список телеграм що відповідають фільтру. "
        "Відповідь — JSON → pandas DataFrame → Plotly chart."
    )

    # Формуємо payload для POST запиту
    payload: dict = {"country_code": country, "station_id": station_id}
    if use_date and selected_date:
        payload["date"] = selected_date.strftime("%Y%m%d")
    if selected_fields:
        payload["fields_to_return"] = selected_fields

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**JSON body запиту:**")
        st.json(payload)
    with col2:
        st.markdown("&nbsp;")
        fetch_btn = st.button("🔍 Виконати запит", type="primary", use_container_width=True)

    if fetch_btn:
        # ── КЛЮЧОВИЙ МОМЕНТ ──────────────────────────────────────────────
        # requests.post() серіалізує `payload` у JSON bytes,
        # відкриває TCP-з'єднання до FastAPI, надсилає HTTP запит,
        # БЛОКУЄТЬСЯ і чекає відповідь.
        # ─────────────────────────────────────────────────────────────────
        with st.spinner("Виконую POST запит... (Python блокується і чекає)"):
            result = make_request("POST", f"{api_url}/filter_telegrams/", json=payload)
        st.session_state["last_result"] = result

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        ok = show_status(result)

        if ok:
            body = result["response_body"]

            if isinstance(body, dict) and "results" in body:
                records = body["results"]

                if not records:
                    st.info(
                        "📭 База порожня. Перейди на вкладку **⬇️ Завантажити з Ogimet** "
                        "щоб заповнити MongoDB."
                    )
                else:
                    st.metric("Знайдено записів", len(records))

                    # JSON → list[dict] → pandas DataFrame
                    data_list = [r.get("data", r) for r in records]
                    df = pd.DataFrame(data_list)

                    st.markdown("**pandas DataFrame:**")
                    st.dataframe(df, use_container_width=True)

                    # Plotly chart якщо є temperature
                    if "temperature" in df.columns and df["temperature"].notna().any():
                        st.markdown("**Plotly Express — температура:**")

                        if all(c in df.columns for c in ["year", "month", "day", "hour"]):
                            df["datetime"] = pd.to_datetime(
                                df[["year", "month", "day", "hour"]]
                            )
                            x_col = "datetime"
                        else:
                            x_col = df.index.astype(str)

                        fig = px.line(
                            df.dropna(subset=["temperature"]),
                            x=x_col,
                            y="temperature",
                            title=f"Температура — {station_name} (WMO {station_id})",
                            labels={"temperature": "°C", "datetime": "Дата/час"},
                            markers=True,
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with st.expander("📦 Raw JSON відповідь"):
                        st.json(body)
            else:
                st.json(body)

# ───────────────────────────────────────────────────────────────────────────
# TAB 2: Завантажити з Ogimet — POST /download_telegrams
# ───────────────────────────────────────────────────────────────────────────
with tab_download:
    st.subheader("POST /download_telegrams")

    st.markdown("""
    Цей endpoint **запускає синхронне завантаження** телеграм з [ogimet.com](http://www.ogimet.com).

    > **Пастка для початківців — Blocking I/O!**
    > Endpoint обходить 35+ станцій **по одній**, кожна — окремий HTTP-запит.
    > Python блокується на кожному `requests.get()`.
    > Весь процес займає **1–5 хвилин**.
    > Якщо ogimet.com недоступний — отримаєш `ConnectionError`.
    """)

    st.markdown("**Еквівалентний Python код:**")
    st.code(
        f"""
import requests

# POST-запит із query parameter (не JSON body!)
# country_code передається в URL: ?country_code=ua
response = requests.post(
    "{api_url}/download_telegrams",
    params={{"country_code": "{country}"}},
    timeout=(5.0, 600.0),   # 10 хвилин read timeout!
)

print(response.status_code)   # 200
print(response.json())
# {{"message": "Successfully downloaded telegrams for 'ua'"}}
        """,
        language="python",
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        download_btn = st.button(
            f"⬇️ Завантажити '{country}'",
            type="primary",
            use_container_width=True,
        )
    with col2:
        st.warning("⏳ Процес займає 1–5 хвилин. Чекай на повідомлення.")

    if download_btn:
        with st.spinner(
            f"Завантажую телеграми для '{country}'... Python блокується, чекаємо..."
        ):
            result = make_request(
                "POST",
                f"{api_url}/download_telegrams",
                params={"country_code": country},
            )

        show_status(result)
        if result["response_body"]:
            st.json(result["response_body"])

# ───────────────────────────────────────────────────────────────────────────
# TAB 3: CRUD операції — GET / PUT / DELETE
# ───────────────────────────────────────────────────────────────────────────
with tab_crud:
    st.subheader("CRUD операції — GET / PUT / DELETE")

    st.markdown("""
    | HTTP метод | CRUD | Idempotent? | Приклад |
    |------------|------|-------------|---------|
    | **GET**    | Read | ✅ Так | отримати запис по ID |
    | **POST**   | Create / пошук | ❌ Ні | фільтрувати, завантажити |
    | **PUT**    | Update | ✅ Так | оновити температуру |
    | **DELETE** | Delete | ✅ Так | видалити запис |

    **ID телеграми** формується як: `{station_id}{year}{month}{day}{hour}`
    Наприклад: `3450420249218` = станція 34504, 2024-09-02 18:00
    """)

    # ── GET ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### GET /telegram/{collection}/{id}")

    col1, col2 = st.columns([3, 1])
    with col1:
        get_id = st.text_input(
            "ID телеграми",
            key="get_id",
            placeholder="3450420249218",
        )
    with col2:
        get_coll = st.selectbox("Колекція", ["ua", "bel"], key="get_coll")

    if st.button("🔍 GET — отримати", use_container_width=False):
        if get_id.strip():
            r = make_request("GET", f"{api_url}/telegram/{get_coll}/{get_id.strip()}")
            show_status(r)
            if r["response_body"]:
                st.json(r["response_body"])

    # ── PUT ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### PUT /telegram/{collection}/{id} — оновити поле")

    col1, col2 = st.columns([3, 1])
    with col1:
        put_id = st.text_input("ID для оновлення", key="put_id", placeholder="3450420249218")
    with col2:
        put_coll = st.selectbox("Колекція", ["ua", "bel"], key="put_coll")

    col1, col2 = st.columns(2)
    with col1:
        update_field = st.text_input("Поле", value="temperature", key="put_field")
    with col2:
        update_value = st.text_input("Нове значення", value="25.0", key="put_value")

    st.markdown(
        "**Тіло запиту (JSON):** " +
        f'`{{"{update_field}": {update_value}}}`'
    )

    if st.button("✏️ PUT — оновити"):
        if put_id.strip():
            try:
                val: float | str = float(update_value)
            except ValueError:
                val = update_value
            r = make_request(
                "PUT",
                f"{api_url}/telegram/{put_coll}/{put_id.strip()}",
                json={update_field: val},
            )
            show_status(r)
            if r["response_body"]:
                st.json(r["response_body"])

    # ── DELETE ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### DELETE /telegram/{collection}/{id}")

    col1, col2 = st.columns([3, 1])
    with col1:
        del_id = st.text_input("ID для видалення", key="del_id", placeholder="3450420249218")
    with col2:
        del_coll = st.selectbox("Колекція", ["ua", "bel"], key="del_coll")

    if st.button("🗑️ DELETE — видалити", type="secondary"):
        if del_id.strip():
            r = make_request("DELETE", f"{api_url}/telegram/{del_coll}/{del_id.strip()}")
            show_status(r)
            if r["response_body"]:
                st.json(r["response_body"])

# ───────────────────────────────────────────────────────────────────────────
# TAB 4: HTTP Inspector
# ───────────────────────────────────────────────────────────────────────────
with tab_inspector:
    st.subheader("🔬 HTTP Inspector — деталі запиту/відповіді")

    st.markdown("""
    Тут видно **точні байти HTTP-обміну** між Streamlit (клієнт) та FastAPI (сервер).
    Виконай запит на вкладці **📊 Дані та Графік** щоб побачити деталі.

    > **Ключова концепція:** `response.request` — це `PreparedRequest`,
    > тобто точні заголовки і тіло, що були надіслані по TCP.
    """)

    if "last_result" not in st.session_state:
        st.info("Спочатку виконай запит на вкладці 📊")
    else:
        result = st.session_state["last_result"]

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Метод", result["method"])
        col2.metric("Status Code", result.get("status_code", "—"))
        col3.metric("Час", f"{result.get('elapsed_ms', '—')} ms")
        col4.metric(
            "Розмір відповіді",
            f"{len(json.dumps(result.get('response_body', '')))} bytes",
        )

        st.markdown(f"**URL:** `{result['url']}`")

        # HTTP Status meaning
        code = result.get("status_code")
        status_meanings = {
            200: "200 OK — запит успішний, дані у відповіді",
            201: "201 Created — ресурс створено",
            204: "204 No Content — успіх, відповідь порожня",
            400: "400 Bad Request — некоректний запит",
            404: "404 Not Found — ресурс не існує",
            422: "422 Unprocessable Entity — помилка валідації Pydantic",
            500: "500 Internal Server Error — помилка сервера",
        }
        if code in status_meanings:
            st.info(f"ℹ️ {status_meanings[code]}")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📤 REQUEST (що відправили)")
            st.markdown("**Headers:**")
            st.json(result.get("request_headers", {}))

            st.markdown("**Body:**")
            body = result.get("request_body")
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            if body:
                try:
                    st.json(json.loads(body))
                except Exception:
                    st.code(body, language="text")
            else:
                st.caption("_(порожнє тіло)_")

        with col2:
            st.markdown("#### 📥 RESPONSE (що отримали)")
            st.markdown("**Headers:**")
            resp_headers = result.get("response_headers", {})
            # Виділяємо важливі заголовки
            important = {
                k: v for k, v in resp_headers.items()
                if k.lower() in ("content-type", "content-length", "server", "date",
                                  "x-process-time")
            }
            st.json(important if important else resp_headers)

            st.markdown("**Body (перші 5 записів):**")
            resp_body = result.get("response_body", {})
            if isinstance(resp_body, dict) and "results" in resp_body:
                preview = {
                    "results": resp_body["results"][:5],
                    "_total": len(resp_body["results"]),
                }
                st.json(preview)
            else:
                st.json(resp_body)

        # HTTP conversation text view
        with st.expander("📝 HTTP як текст (як виглядає по дроту)"):
            req_body_str = result.get("request_body", "")
            if isinstance(req_body_str, bytes):
                req_body_str = req_body_str.decode("utf-8")

            headers_str = "\n".join(
                f"{k}: {v}" for k, v in result.get("request_headers", {}).items()
            )
            st.code(
                f"""{result['method']} /filter_telegrams/ HTTP/1.1
{headers_str}

{req_body_str or '(empty)'}

──── RESPONSE ────
HTTP/1.1 {result.get('status_code')} OK
{chr(10).join(f'{k}: {v}' for k, v in list(result.get('response_headers', {}).items())[:8])}

(JSON body вище)
""",
                language="text",
            )

# ───────────────────────────────────────────────────────────────────────────
# TAB 5: API Guide
# ───────────────────────────────────────────────────────────────────────────
with tab_guide:
    st.subheader("📚 API Guide — як тестувати API")

    st.markdown(f"""
    ### Swagger UI — інтерактивна документація

    FastAPI автоматично генерує Swagger/OpenAPI документацію.
    Відкрий у браузері: **[{api_url}/docs]({api_url}/docs)**

    Swagger дозволяє:
    - Бачити всі endpoints з описами
    - Виконувати запити прямо в браузері
    - Бачити схеми `request` / `response` (Pydantic models)
    - Генерувати curl команди

    ---
    ### curl — HTTP з командного рядка
    """)

    st.code(
        f"""# ── GET — отримати телеграму по ID
curl -X GET \\
  "{api_url}/telegram/ua/3450420249218"

# ── POST — фільтрувати телеграми
curl -X POST \\
  "{api_url}/filter_telegrams/" \\
  -H "Content-Type: application/json" \\
  -d '{{"country_code": "ua", "station_id": "33345", "fields_to_return": ["temperature", "year", "month", "day", "hour"]}}'

# ── POST — завантажити нові дані з ogimet.com
curl -X POST \\
  "{api_url}/download_telegrams?country_code=ua"

# ── PUT — оновити поле
curl -X PUT \\
  "{api_url}/telegram/ua/3450420249218" \\
  -H "Content-Type: application/json" \\
  -d '{{"temperature": 25.5}}'

# ── DELETE — видалити запис
curl -X DELETE \\
  "{api_url}/telegram/ua/3450420249218"
""",
        language="bash",
    )

    st.markdown("### Python requests — повторити у Jupyter Notebook")

    st.code(
        f"""import requests

BASE_URL = "{api_url}"

# ── POST /filter_telegrams/ ─────────────────────────────────────
payload = {{
    "country_code": "ua",
    "station_id": "33345",   # Київ
    "fields_to_return": ["year", "month", "day", "hour", "temperature"],
}}

response = requests.post(
    f"{{BASE_URL}}/filter_telegrams/",
    json=payload,                          # серіалізує dict у JSON bytes
    headers={{"Content-Type": "application/json"}},
    timeout=(5.0, 60.0),                   # завжди встановлюй timeout!
)

# Перевіряємо статус
print(response.status_code)   # 200
response.raise_for_status()   # кидає HTTPError якщо 4xx/5xx

# Десеріалізуємо JSON відповідь
data = response.json()
records = data["results"]

# pandas
import pandas as pd
df = pd.DataFrame([r["data"] for r in records])
print(df[["year", "month", "day", "hour", "temperature"]].head())

# ── GET /telegram/ua/{{id}} ─────────────────────────────────────
response = requests.get(f"{{BASE_URL}}/telegram/ua/3450420249218")
telegram = response.json()
print(telegram)

# ── PUT — оновити температуру ───────────────────────────────────
response = requests.put(
    f"{{BASE_URL}}/telegram/ua/3450420249218",
    json={{"temperature": 25.5}},
    timeout=(5.0, 10.0),
)
print(response.json())   # {{"message": "Запис успішно оновлено"}}

# ── DELETE ──────────────────────────────────────────────────────
response = requests.delete(f"{{BASE_URL}}/telegram/ua/3450420249218")
print(response.json())
""",
        language="python",
    )

    st.markdown("### ngrok — публічний URL для локального API")

    st.code(
        """# 1. Запусти Docker stack
docker compose up --build

# 2. В окремому терміналі — запусти ngrok
ngrok http 8000

# 3. Отримаєш публічний URL:
#    Forwarding  https://d247-xxxx.ngrok-free.app -> http://localhost:8000

# 4. Відкрий Swagger студентам:
#    https://d247-xxxx.ngrok-free.app/docs

# 5. Студенти можуть тестувати з будь-якого місця!
""",
        language="bash",
    )

    st.markdown("### HTTP Status Codes — шпаргалка")

    status_data = {
        "Код": [200, 201, 204, 400, 404, 422, 500],
        "Назва": [
            "OK", "Created", "No Content",
            "Bad Request", "Not Found", "Unprocessable Entity",
            "Internal Server Error",
        ],
        "Коли": [
            "Запит успішний",
            "Ресурс створено (POST)",
            "Успіх, але тіло порожнє",
            "Некоректний запит від клієнта",
            "Ресурс не існує",
            "Pydantic не прийняв body",
            "Помилка на сервері",
        ],
    }
    st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════
st.divider()
st.caption(
    f"Урок 31 — HTTP & REST API | FastAPI: [{api_url}/docs]({api_url}/docs) "
    f"| Streamlit + requests + pandas + plotly"
)
