"""
LUFT LOGISTICS — Sistema de Controle de Motoristas
Versão Streamlit — arquivo único (app.py)

Coloque na mesma pasta:
  • luft.png       — imagem de fundo da splash
  • credentials.json — credenciais Google Service Account

Execute com:
  streamlit run app.py
"""
#  python3 -m streamlit run app.py


import json
import base64
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import gspread
from google.oauth2.service_account import Credentials
import google.auth.transport.requests

# ─── Configurações ────────────────────────────────────────────────────────────
SHEET_ID   = "1o_P9PLrdFf9wkVz6p2aQ_-2vnK1LYOzozOvVU0PJlxc"
SHEET_NAME = "motoristas_luft"
# Credenciais: arquivo credentials.json na mesma pasta do app.py
BASE_DIR         = Path(__file__).parent
CREDENTIALS_PATH = BASE_DIR / "gestaodefrota-498416-b86f8b663ae2.json"
LOGO_PATH        = BASE_DIR / "luft.png"

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

COLUNAS = [
    "cpf", "nome", "filial", "telefone", "email", "foto",
    "reciclagem", "simulador",
    "excesso", "multas", "acidentes",
    "obsAcidente", "obsMultas", "obsGerais", "obsReciclagem", "obsSimulador",
    "cnh", "validadeCnh", "admissao",
]
for _mes in MESES:
    for _s in range(1, 5):
        COLUNAS.append(f"dss_{_mes}_{_s}")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ─── Google Sheets helpers ────────────────────────────────────────────────────
def get_sheet():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(COLUNAS) + 5)
        ws.append_row(COLUNAS)
    return ws

def ler_todos_motoristas():
    ws = get_sheet()
    records = ws.get_all_records(default_blank="")
    motoristas = []
    for row in records:
        if not row.get("cpf"):
            continue
        dss_anual = {}
        for mes in MESES:
            semanas = []
            for s in range(1, 5):
                val = row.get(f"dss_{mes}_{s}", "")
                semanas.append(bool(val) and val not in ("", "0", 0, False))
            dss_anual[mes] = semanas
        motoristas.append({
            "cpf":           str(row.get("cpf", "")).strip(),
            "nome":          str(row.get("nome", "")).strip(),
            "filial":        str(row.get("filial", "")).strip(),
            "telefone":      str(row.get("telefone", "")).strip(),
            "email":         str(row.get("email", "")).strip(),
            "foto":          str(row.get("foto", "")).strip(),
            "reciclagem":    str(row.get("reciclagem", "PENDENTE")).strip() or "PENDENTE",
            "simulador":     str(row.get("simulador", "PENDENTE")).strip() or "PENDENTE",
            "excesso":       max(0, int(row.get("excesso", 0) or 0)),
            "multas":        max(0, int(row.get("multas", 0) or 0)),
            "acidentes":     max(0, int(row.get("acidentes", 0) or 0)),
            "obsAcidente":   str(row.get("obsAcidente", "")).strip(),
            "obsMultas":     str(row.get("obsMultas", "")).strip(),
            "obsGerais":     str(row.get("obsGerais", "")).strip(),
            "obsReciclagem": str(row.get("obsReciclagem", "")).strip(),
            "obsSimulador":  str(row.get("obsSimulador", "")).strip(),
            "cnh":           str(row.get("cnh", "")).strip(),
            "validadeCnh":   str(row.get("validadeCnh", "")).strip(),
            "admissao":      str(row.get("admissao", "")).strip(),
            "dssAnual":      dss_anual,
        })
    return motoristas


def salvar_todos_motoristas(lista):
    ws = get_sheet()
    all_rows = []
    for m in lista:
        row_data = [
            m.get("cpf", ""), m.get("nome", ""), m.get("filial", ""),
            m.get("telefone", ""), m.get("email", ""), m.get("foto", ""),
            m.get("reciclagem", "PENDENTE"), m.get("simulador", "PENDENTE"),
            m.get("excesso", 0), m.get("multas", 0), m.get("acidentes", 0),
            m.get("obsAcidente", ""), m.get("obsMultas", ""), m.get("obsGerais", ""),
            m.get("obsReciclagem", ""), m.get("obsSimulador", ""),
            m.get("cnh", ""), m.get("validadeCnh", ""), m.get("admissao", ""),
        ]
        dss = m.get("dssAnual", {})
        for mes in MESES:
            semanas = dss.get(mes, [False] * 4)
            for s in range(4):
                row_data.append(1 if (len(semanas) > s and semanas[s]) else 0)
        all_rows.append(row_data)
    existing = ws.get_all_values()
    if len(existing) > 1:
        ws.delete_rows(2, len(existing))
    if all_rows:
        ws.append_rows(all_rows, value_input_option="USER_ENTERED")


# ─── Gera access token OAuth2 para o JS usar ─────────────────────────────────
def get_access_token():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

# ─── Logo em base64 ───────────────────────────────────────────────────────────
def logo_b64():
    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


# ─── Streamlit page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="LUFT Logistics — Controle de Motoristas",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Oculta elementos padrão do Streamlit (menu, footer, padding)
st.markdown("""
<style>
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  [data-testid="stAppViewContainer"] { padding: 0 !important; }
  [data-testid="stVerticalBlock"] { gap: 0 !important; }
  iframe { height: 100vh !important; min-height: 100vh !important; }
  [data-testid="stIFrame"] { height: 100vh !important; }
</style>
""", unsafe_allow_html=True)

# ─── HTML completo da aplicação ───────────────────────────────────────────────
_LOGO_B64 = logo_b64()
_LOGO_CSS  = (
    f"background:url('data:image/png;base64,{_LOGO_B64}') center center/cover no-repeat;"
    if _LOGO_B64 else
    "background:linear-gradient(135deg,#0a1440 0%,#1a3a6b 100%);"
)
_ACCESS_TOKEN = get_access_token()

HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LUFT Logistics — Controle de Motoristas</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}

/* ── TELA SPLASH ── */
#splash-screen{{
  position:fixed;top:0;left:0;width:100vw;height:100vh;
  z-index:999999;
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;
}}
#splash-bg{{
  position:absolute;top:0;left:0;width:100%;height:100%;
  {_LOGO_CSS}
  filter:brightness(1);
}}
.splash-card{{
  position:relative;z-index:2;
  background:rgba(10,20,60,0.82);
  border:1.5px solid rgba(59,125,216,0.45);
  border-radius:16px;
  padding:40px 48px;
  text-align:center;
  backdrop-filter:blur(12px);
  box-shadow:0 24px 64px rgba(0,0,0,0.6);
  min-width:360px;
  max-width:480px;
}}
.splash-logo-txt{{font-size:36px;font-weight:900;color:#ffffff;letter-spacing:-1px;margin-bottom:4px}}
.splash-logo-txt span{{color:#22cc88}}
.splash-sub{{font-size:11px;letter-spacing:3px;color:#8ab4d8;text-transform:uppercase;margin-bottom:32px}}
.splash-label{{font-size:12px;color:#8ab4d8;letter-spacing:1px;text-transform:uppercase;font-weight:700;margin-bottom:12px}}
.splash-drop-area{{border:2px dashed rgba(59,125,216,0.5);border-radius:10px;padding:28px 20px;cursor:pointer;transition:all .2s;background:rgba(59,125,216,0.07);margin-bottom:14px}}
.splash-drop-area:hover,.splash-drop-area.drag-over{{border-color:#3b7dd8;background:rgba(59,125,216,0.18)}}
.splash-drop-icon{{font-size:32px;color:#3b7dd8;margin-bottom:8px}}
.splash-drop-txt{{font-size:13px;color:#a0bcd8;line-height:1.5}}
.splash-drop-txt strong{{color:#ffffff}}
#splashFileInput{{display:none}}
.splash-btn-escolher{{display:inline-block;margin-top:10px;background:#3b7dd8;color:#fff;padding:8px 22px;border-radius:6px;font-size:12px;font-weight:700;letter-spacing:1px;cursor:pointer;border:none;text-transform:uppercase;transition:background .2s}}
.splash-btn-escolher:hover{{background:#2563b0}}
.splash-status{{font-size:12px;color:#22cc88;margin-top:10px;min-height:18px;font-weight:600;letter-spacing:.5px}}
.splash-status.erro{{color:#ff4444}}
.splash-progress{{display:none;width:100%;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;margin-top:12px;overflow:hidden}}
.splash-progress-bar{{height:100%;width:0%;background:#3b7dd8;border-radius:2px;transition:width .3s;animation:progressAnim .8s ease-in-out infinite alternate}}
@keyframes progressAnim{{0%{{opacity:.6}}100%{{opacity:1}}}}

/* ── TEMA GLOBAL ── */
.db{{background:#f0f4fa;color:#1a2a44;font-family:'Segoe UI',sans-serif;padding:0;font-size:14px}}

/* ── TOP BAR ── */
.top-bar{{background:#ffffff;border-bottom:2px solid #dde6f4;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 8px rgba(20,50,120,0.07)}}
.brand{{display:flex;align-items:center;gap:10px}}
.brand-logo{{background:#f0f4fa;border:1.5px solid #c4d0e4;border-radius:6px;padding:6px 14px;display:flex;align-items:center;gap:8px}}
.dot-anim{{width:10px;height:10px;border-radius:50%;background:#e53e3e;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.brand-name{{font-size:13px;font-weight:700;letter-spacing:2px;color:#1a3a6b;text-transform:uppercase}}
.brand-sub{{font-size:11px;color:#1a7a4a;letter-spacing:1px}}
.luft-name{{font-size:26px;font-weight:900;color:#1a3a6b;letter-spacing:-1px}}
.luft-name span{{color:#1a7a4a}}
.pct-box{{background:#f0f4fa;border:1.5px solid #c4d0e4;border-radius:6px;padding:6px 14px;text-align:right}}
.pct-lbl{{font-size:11px;color:#5a6e8a;letter-spacing:1px;text-transform:uppercase;font-weight:600}}
.pct-val{{font-size:30px;font-weight:900;color:#16a34a}}

/* ── CONTEÚDO ── */
.content{{padding:12px 14px}}

/* ── KPIs ── */
.kpi-row{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:16px}}
.kpi{{border-radius:10px;padding:18px 20px;border:2px solid}}
.kpi.red{{background:#fff5f5;border-color:#ff4444;box-shadow:0 0 10px rgba(255,68,68,0.35),inset 0 0 6px rgba(255,68,68,0.06)}}
.kpi.green{{background:#f0fef4;border-color:#22cc88;box-shadow:0 0 10px rgba(34,204,136,0.35),inset 0 0 6px rgba(34,204,136,0.06)}}
.kpi.amber{{background:#fffbeb;border-color:#ffaa00;box-shadow:0 0 10px rgba(255,170,0,0.35),inset 0 0 6px rgba(255,170,0,0.06)}}
.kpi.blue{{background:#f0f6ff;border-color:#3b7dd8;box-shadow:0 0 10px rgba(59,125,216,0.35),inset 0 0 6px rgba(59,125,216,0.06)}}
.kpi-lbl{{font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:#5a6e8a;margin-bottom:6px;font-weight:700}}
.kpi-val{{font-size:52px;font-weight:900;line-height:1}}
.kpi.red .kpi-val{{color:#dc2626}}
.kpi.green .kpi-val{{color:#16a34a}}
.kpi.amber .kpi-val{{color:#d97706}}
.kpi.blue .kpi-val{{color:#1a4fa0}}
.kpi-sub{{font-size:12px;color:#3b7dd8;margin-top:8px;text-transform:uppercase;letter-spacing:1px;font-weight:600}}

/* ── PAINEL / SEÇÕES ── */
.sec-title{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#1a4fa0;margin-bottom:8px;display:flex;align-items:center;gap:6px}}
.sec-title::before{{content:'';display:inline-block;width:3px;height:10px;background:#3b7dd8;border-radius:2px}}
.panel{{background:#ffffff;border:1.5px solid #dde6f4;border-radius:10px;padding:12px;margin-bottom:12px;box-shadow:0 2px 8px rgba(20,50,120,0.06)}}

/* ── GRID FILIAIS ── */
.filial-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.fc{{background:#f8fafd;border:1.5px solid #c4d0e4;border-radius:10px;padding:14px;display:flex;flex-direction:column;justify-content:space-between}}
.fc-name{{font-size:20px;font-weight:800;color:#1a3a6b;margin-bottom:6px}}
.fc-count{{font-size:48px;font-weight:900;line-height:1;margin-bottom:10px;color:#1a4fa0}}
.situation-bars{{display:flex;flex-direction:column;gap:6px}}
.sbar{{display:flex;align-items:center;gap:8px}}
.sbar-lbl{{font-size:13px;color:#5a6e8a;width:66px;flex-shrink:0;text-transform:uppercase;letter-spacing:.5px;font-weight:700}}
.sbar-track{{flex:1;height:7px;background:#e0e8f0;border-radius:3px;overflow:hidden}}
.sbar-fill{{height:100%;border-radius:3px;transition:width .3s}}
.sbar-cnt{{font-size:15px;font-weight:700;width:28px;text-align:right;flex-shrink:0}}
.sbar.ok .sbar-fill{{background:#16a34a}}.sbar.ok .sbar-cnt{{color:#16a34a}}
.sbar.neg .sbar-fill{{background:#dc2626}}.sbar.neg .sbar-cnt{{color:#dc2626}}
.sbar.pend .sbar-fill{{background:#d97706}}.sbar.pend .sbar-cnt{{color:#d97706}}

/* ── GRÁFICOS ── */
.chart-wrap{{position:relative;width:100%}}
.leg{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px}}
.leg-item{{display:flex;align-items:center;gap:4px;font-size:14px;color:#5a6e8a;font-weight:600}}
.leg-sq{{width:9px;height:9px;border-radius:1px;flex-shrink:0}}
.btn-zoom{{background:rgba(59,125,216,0.07);color:#3b7dd8;border:1px solid rgba(59,125,216,0.2);border-radius:4px;padding:8px;font-size:13px;font-weight:700;cursor:pointer;text-transform:uppercase;text-align:center;margin-top:8px;display:flex;align-items:center;justify-content:center;gap:4px}}
.btn-zoom:hover{{background:#3b7dd8;color:#fff}}

/* ── TOAST ── */
.toast{{position:fixed;bottom:24px;right:24px;background:#ffffff;border:1.5px solid #c4d0e4;color:#1a2a44;padding:12px 20px;border-radius:8px;font-size:13px;z-index:99999;display:none;gap:10px;align-items:center;box-shadow:0 8px 24px rgba(20,50,120,0.15)}}
.toast.ok{{border-color:#86efac;color:#16a34a}}
.toast.erro{{border-color:#fca5a5;color:#dc2626}}
.toast.show{{display:flex}}

/* ── SPINNER ── */
.spinner-overlay{{position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(240,244,250,0.75);z-index:88888;display:none;align-items:center;justify-content:center}}
.spinner-overlay.show{{display:flex}}
.spinner{{width:44px;height:44px;border:4px solid #dde6f4;border-top-color:#3b7dd8;border-radius:50%;animation:spin 0.8s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}

/* ── MODAL FILIAL ── */
.modal-overlay{{position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(20,40,100,0.45);backdrop-filter:blur(8px);display:none;justify-content:center;align-items:center;z-index:9999}}
.modal-box{{background:#ffffff;border:1.5px solid #dde6f4;width:100%;max-width:100%;height:100vh;border-radius:0;padding:20px;display:flex;flex-direction:column;gap:12px;box-shadow:0 16px 48px rgba(20,50,120,0.18)}}
.modal-header{{display:flex;justify-content:space-between;align-items:center;border-bottom:1.5px solid #dde6f4;padding-bottom:10px}}
.modal-title{{font-size:18px;font-weight:800;color:#1a3a6b;text-transform:uppercase;display:flex;align-items:center;gap:8px}}
.btn-close{{background:#7a1a1a;color:#ffffff;border:1px solid #5c1212;width:28px;height:28px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.btn-close:hover{{background:#ff2222;color:#fff;border-color:#ff4444;box-shadow:0 0 10px rgba(255,50,50,0.7),0 0 20px rgba(255,50,50,0.4)}}
.modal-split{{display:grid;grid-template-columns:280px 1fr;gap:14px;flex:1;overflow:hidden}}
.modal-sidebar{{display:flex;flex-direction:column;gap:8px}}
.modal-kpi-card{{background:#f8fafd;border:1.5px solid #dde6f4;padding:14px;border-radius:8px;cursor:pointer;transition:border-color .15s,box-shadow .15s}}
.modal-kpi-card:hover{{border-color:#3b7dd8;box-shadow:0 2px 12px rgba(59,125,216,0.18)}}
.m-lbl{{font-size:12px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:1px}}
.m-val{{font-size:36px;font-weight:900;color:#1a3a6b}}
.modal-main{{background:#f8fafd;border:1.5px solid #dde6f4;border-radius:8px;display:flex;flex-direction:column;overflow:hidden}}
.table-container{{flex:1;overflow-y:auto}}
.m-table{{width:100%;border-collapse:collapse;text-align:left;font-size:14px}}
.m-table th{{background:#eef3fb;color:#1a4fa0;font-size:12px;font-weight:800;text-transform:uppercase;padding:14px 16px;border-bottom:1.5px solid #dde6f4;position:sticky;top:0}}
.m-table td{{padding:14px 16px;border-bottom:1px solid #eef3fb;color:#2a3a55}}
.driver-row{{cursor:pointer}}
.driver-row:hover{{background:#eef3fb!important}}
.m-name{{font-weight:700;color:#1a3a6b;font-size:15px}}
.m-cpf{{font-family:monospace;font-size:13px;color:#5a6e8a}}
.m-badge{{display:inline-block;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:700}}
.m-badge.ok{{background:rgba(22,163,74,0.1);color:#16a34a;border:1px solid rgba(22,163,74,0.25)}}
.m-badge.pend{{background:rgba(217,119,6,0.1);color:#d97706;border:1px solid rgba(217,119,6,0.25)}}
.m-count-badge{{font-weight:700;color:#1a3a6b;background:#eef3fb;padding:4px 10px;border-radius:4px;border:1px solid #c4d0e4;font-size:14px}}

/* ── FORMULÁRIO ── */
.admin-panel{{background:#ffffff;border:1.5px solid #c4d0e4;border-radius:10px;margin-bottom:12px;overflow:hidden;box-shadow:0 2px 8px rgba(20,50,120,0.06)}}
.admin-panel-header{{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;cursor:pointer;user-select:none}}
.admin-panel-header:hover{{background:#f4f8ff}}
.admin-panel-title{{display:flex;align-items:center;gap:10px;font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#16a34a}}
.admin-panel-title::before{{content:'';display:inline-block;width:3px;height:10px;background:#16a34a;border-radius:2px}}
.btn-toggle-form{{background:rgba(22,163,74,0.08);color:#16a34a;border:1px solid rgba(22,163,74,0.3);border-radius:5px;padding:8px 16px;font-size:13px;font-weight:700;text-transform:uppercase;cursor:pointer;display:flex;align-items:center;gap:6px;transition:.2s}}
.btn-toggle-form:hover{{background:#16a34a;color:#fff}}
.btn-toggle-form .chevron{{transition:transform .3s}}
.btn-toggle-form.open .chevron{{transform:rotate(180deg)}}
.admin-panel-body{{max-height:0;overflow:hidden;transition:max-height .35s ease,padding .35s ease;padding:0 16px}}
.admin-panel-body.open{{max-height:200px;padding:0 16px 16px}}
.form-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:10px}}
.form-group{{display:flex;flex-direction:column;gap:4px}}
.form-group label{{font-size:13px;color:#5a6e8a;text-transform:uppercase;font-weight:700}}
.form-group input,.form-group select{{background:#f4f7fc;border:1px solid #c4d0e4;color:#1a2a44;padding:8px 12px;border-radius:4px;font-size:14px;outline:none}}
.form-group input:focus,.form-group select:focus{{border-color:#3b7dd8;background:#fff}}
.btn-add{{background:#16a34a;color:#fff;border:none;font-weight:700;text-transform:uppercase;cursor:pointer;padding:0 16px;border-radius:4px;height:32px;margin-top:17px;display:flex;align-items:center;justify-content:center;gap:6px;font-size:11px}}
.btn-add:hover{{background:#15803d}}
.btn-save-master{{background:transparent;color:#16a34a;border:1.5px solid #16a34a;padding:7px 20px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;border-radius:6px;cursor:pointer;display:flex;align-items:center;gap:7px;transition:color .2s,border-color .2s,box-shadow .2s,background .2s}}
.btn-save-master:hover{{background:transparent;color:#dc2626;border-color:#dc2626;box-shadow:0 0 12px rgba(220,38,38,0.18)}}

/* ── FICHA INDIVIDUAL ── */
.driver-profile-grid{{display:grid;grid-template-columns:340px 1fr;gap:16px;padding:18px;background:#f0f4fa}}
.profile-details-right{{display:flex;flex-direction:column;gap:14px}}
.info-section-box{{background:#ffffff;border-radius:12px;padding:0;overflow:hidden;box-shadow:0 2px 8px rgba(20,50,120,0.08);border:1.5px solid #dde6f4;transition:box-shadow .2s}}
.info-section-box:hover{{box-shadow:0 4px 16px rgba(20,50,120,0.13)}}
.card-stripe{{height:4px;width:100%;border-radius:0;display:block}}
.card-body{{padding:14px 16px 16px}}
.info-block-title{{font-size:14px;font-weight:800;text-transform:uppercase;letter-spacing:.8px;border-bottom:1px solid #e8eef8;padding-bottom:6px;margin-bottom:12px;display:flex;align-items:center;gap:7px}}
.card-condutor{{border-color:#3b7dd8}}
.card-condutor .card-stripe{{background:linear-gradient(90deg,#1a4fa0,#3b7dd8)}}
.card-condutor .info-block-title{{color:#1a4fa0}}
.avatar-wrapper{{position:relative;width:92px;height:92px;margin:0 auto;cursor:pointer;border-radius:50%;border:2.5px dashed #3b7dd8;overflow:hidden;display:flex;align-items:center;justify-content:center;background:#e8f0fe}}
.avatar-wrapper img{{width:100%;height:100%;object-fit:cover}}
.avatar-wrapper .upload-hint{{position:absolute;bottom:0;background:rgba(26,79,160,0.82);width:100%;font-size:8px;color:#fff;padding:2px 0;text-transform:uppercase;font-weight:700}}
.profile-card-left{{background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(20,50,120,0.10);border:1.5px solid #3b7dd8;display:flex;flex-direction:column}}
.profile-card-left .card-stripe{{background:linear-gradient(90deg,#1a4fa0,#3b7dd8)}}
.profile-card-left-body{{padding:16px;text-align:center;display:flex;flex-direction:column;gap:10px;flex:1;justify-content:space-between}}
.card-contato{{border-color:#0e9cc0}}
.card-contato .card-stripe{{background:linear-gradient(90deg,#0a7a9a,#0eb8e0)}}
.card-contato .info-block-title{{color:#0a7a9a;background:linear-gradient(135deg,#e8f8fc,#f0fcff);margin:-14px -16px 12px;padding:10px 16px 8px;border-radius:0}}
.card-docs{{border-color:#5a5fe8}}
.card-docs .card-stripe{{background:linear-gradient(90deg,#3a3ec8,#6c72f5)}}
.card-docs .info-block-title{{color:#3a3ec8;background:linear-gradient(135deg,#eeeeff,#f4f4ff);margin:-14px -16px 12px;padding:10px 16px 8px;border-radius:0}}
.card-seguranca{{border-color:#d97706}}
.card-seguranca .card-stripe{{background:linear-gradient(90deg,#b45309,#f59e0b)}}
.card-seguranca .info-block-title{{color:#b45309;background:linear-gradient(135deg,#fef5e6,#fff8ed);margin:-14px -16px 12px;padding:10px 16px 8px;border-radius:0}}
.card-dss{{border-color:#16a34a}}
.card-dss .card-stripe{{background:linear-gradient(90deg,#15803d,#22c55e)}}
.card-dss .info-block-title{{color:#15803d;background:linear-gradient(135deg,#ecfdf5,#f0fef8);margin:-14px -16px 12px;padding:10px 16px 8px;border-radius:0}}
@keyframes kpi-pulse-red{{0%,100%{{box-shadow:0 0 0 3px rgba(229,62,62,.20),0 4px 20px rgba(229,62,62,.12)}}50%{{box-shadow:0 0 0 5px rgba(229,62,62,.36),0 6px 28px rgba(229,62,62,.22)}}}}
@keyframes kpi-pulse-orange{{0%,100%{{box-shadow:0 0 0 3px rgba(221,107,32,.20),0 4px 20px rgba(221,107,32,.12)}}50%{{box-shadow:0 0 0 5px rgba(221,107,32,.36),0 6px 28px rgba(221,107,32,.22)}}}}
@keyframes kpi-pulse-green{{0%,100%{{box-shadow:0 0 0 3px rgba(22,163,74,.20),0 4px 20px rgba(22,163,74,.12)}}50%{{box-shadow:0 0 0 5px rgba(22,163,74,.36),0 6px 28px rgba(22,163,74,.22)}}}}
.card-highlight-vel{{border-color:#e53e3e!important;animation:kpi-pulse-red 2s ease-in-out infinite}}
.card-highlight-vel .card-stripe{{background:linear-gradient(90deg,#b91c1c,#e53e3e)!important}}
.card-highlight-mul{{border-color:#dd6b20!important;animation:kpi-pulse-orange 2s ease-in-out infinite}}
.card-highlight-mul .card-stripe{{background:linear-gradient(90deg,#c2410c,#dd6b20)!important}}
.card-highlight-acid{{border-color:#e53e3e!important;animation:kpi-pulse-red 2s ease-in-out infinite}}
.card-highlight-acid .card-stripe{{background:linear-gradient(90deg,#b91c1c,#e53e3e)!important}}
.card-highlight-dss{{border-color:#16a34a!important;animation:kpi-pulse-green 2s ease-in-out infinite}}
.card-highlight-dss .card-stripe{{background:linear-gradient(90deg,#15803d,#22c55e)!important}}
.meta-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.meta-item{{display:flex;flex-direction:column;gap:3px}}
.meta-item label{{font-size:13px;color:#5a6e8a;text-transform:uppercase;font-weight:700}}
.meta-item input,.meta-item select{{background:#f4f7fc;border:1px solid #c4d0e4;color:#1a2a44;padding:8px 10px;border-radius:5px;font-size:16px;outline:none;transition:border-color .15s,background .15s,box-shadow .15s}}
.meta-item input:focus,.meta-item select:focus{{border-color:#3b7dd8;background:#ffffff;box-shadow:0 0 0 2px rgba(59,125,216,.12)}}
.card-contato .meta-item input:focus,.card-contato .meta-item select:focus{{border-color:#0e9cc0;box-shadow:0 0 0 2px rgba(14,156,192,.12)}}
.card-docs .meta-item input:focus,.card-docs .meta-item select:focus{{border-color:#5a5fe8;box-shadow:0 0 0 2px rgba(90,95,232,.12)}}
.card-seguranca .meta-item input:focus,.card-seguranca .meta-item select:focus{{border-color:#d97706;box-shadow:0 0 0 2px rgba(217,119,6,.12)}}
.card-dss .meta-item input:focus,.card-dss .meta-item select:focus{{border-color:#16a34a;box-shadow:0 0 0 2px rgba(22,163,74,.12)}}
.obs-input{{background:#f9fafd!important;border:1px solid #d0daea!important;color:#3a4a62!important;font-size:11px!important;font-style:italic}}
.dss-matrix-container{{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}}
.month-dss-box{{background:#f0faf4;border:1px solid #bbddc8;border-radius:7px;padding:7px}}
.month-name-lbl{{font-size:12px;font-weight:800;color:#15803d;text-transform:uppercase;margin-bottom:4px;text-align:center;border-bottom:1px solid #c8e8d4;padding-bottom:3px}}
.weeks-flex{{display:flex;justify-content:space-between;gap:2px}}
.week-checkbox-label{{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:12px;color:#2d6a4a;cursor:pointer;flex:1;font-weight:600}}
.week-checkbox-label input{{cursor:pointer;accent-color:#16a34a}}
.btn-delete-driver{{background:#fff0f0;color:#cc2222;border:1px solid #e8aaaa;padding:8px;border-radius:7px;font-size:10px;font-weight:700;text-transform:uppercase;cursor:pointer;margin-top:12px;display:flex;align-items:center;justify-content:center;gap:6px;transition:.18s;width:100%}}
.btn-delete-driver:hover{{background:#cc2222;color:#fff;border-color:#cc2222}}
#btnConfirmarFicha:hover{{background:#2ea84a!important;border-color:#22883a!important}}
#btnFecharFicha:hover{{background:#b52222!important;border-color:#8a1818!important}}
#btnVoltarFicha:hover{{background:#b52222!important;border-color:#8a1818!important}}
#driverModal .form-group label{{color:#5a6e8a}}
#driverModal .form-group input,#driverModal .form-group select{{background:#f0f4fb;border:1px solid #bccce0;color:#1a2a44}}
.kpi{{cursor:pointer;transition:transform .15s,box-shadow .15s}}
.kpi:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(20,50,120,0.12)}}

/* ── MODAL KPI ── */
.kpi-modal-overlay{{position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(20,40,100,0.45);backdrop-filter:blur(10px);display:none;justify-content:stretch;align-items:stretch;z-index:11000;padding:12px;box-sizing:border-box}}
.kpi-modal-overlay.show{{display:flex}}
.kpi-modal-box{{background:#ffffff;border:1.5px solid #dde6f4;width:100%;height:100%;max-width:none;max-height:none;border-radius:12px;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 16px 48px rgba(20,50,120,0.18)}}
.kpi-modal-head{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1.5px solid #dde6f4;flex-shrink:0;background:#f8fafd}}
.kpi-modal-head-left{{display:flex;align-items:center;gap:12px}}
.kpi-modal-icon{{width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}}
.kpi-modal-label{{font-size:16px;font-weight:800;color:#1a3a6b;text-transform:uppercase;letter-spacing:1.5px}}
.kpi-modal-count{{font-size:14px;color:#5a6e8a;margin-top:2px}}
.kpi-modal-close{{background:#7a1a1a;color:#ffffff;border:1px solid #5c1212;width:30px;height:30px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0}}
.kpi-modal-close:hover{{background:#ff2222;color:#fff;border-color:#ff4444;box-shadow:0 0 10px rgba(255,50,50,0.7),0 0 20px rgba(255,50,50,0.4)}}
.kpi-modal-search{{padding:10px 20px;border-bottom:1px solid #eef3fb;flex-shrink:0;background:#fff}}
.kpi-modal-search input{{width:100%;background:#f4f7fc;border:1.5px solid #c4d0e4;color:#1a2a44;padding:7px 12px;border-radius:6px;font-size:12px;outline:none}}
.kpi-modal-search input:focus{{border-color:#3b7dd8;background:#fff}}
.kpi-mes-filtro{{display:none;padding:8px 20px 0;gap:6px;flex-wrap:wrap;flex-shrink:0;background:#fff}}
.kpi-mes-filtro.visible{{display:flex}}
.mes-btn{{padding:6px 14px;border-radius:20px;border:1.5px solid #c4d0e4;background:#f4f7fc;color:#5a6e8a;font-size:13px;font-weight:700;cursor:pointer;letter-spacing:.5px;transition:all .15s}}
.mes-btn.ativo{{background:#16a34a;border-color:#16a34a;color:#fff}}
.dmc-semanas{{display:flex;gap:4px;margin-top:3px}}
.dmc-sem{{display:flex;flex-direction:column;align-items:center;gap:2px;flex:1}}
.dmc-sem-lbl{{font-size:11px;color:#8899aa;font-weight:700;text-transform:uppercase}}
.dmc-sem-dot{{width:24px;height:24px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:900}}
.dmc-sem-dot.ok{{background:rgba(22,163,74,0.15);color:#16a34a;border:1px solid rgba(22,163,74,0.35)}}
.dmc-sem-dot.pend{{background:rgba(220,38,38,0.08);color:#dc2626;border:1px solid rgba(220,38,38,0.2)}}
.kpi-cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;padding:20px 24px;overflow-y:auto;flex:1;align-content:start;background:#f0f4fa}}
.driver-mini-card{{background:#ffffff;border:1.5px solid #dde6f4;border-radius:10px;padding:14px;cursor:pointer;transition:border-color .15s,transform .15s,box-shadow .15s;display:flex;flex-direction:column;gap:10px;box-shadow:0 2px 6px rgba(20,50,120,0.06)}}
.driver-mini-card.card-ok{{border-color:rgba(22,163,74,0.45);background:#f0fef4}}
.driver-mini-card.card-pend{{border-color:rgba(217,119,6,0.45);background:#fffbeb}}
.driver-mini-card:hover{{border-color:#3b7dd8;transform:translateY(-2px);box-shadow:0 8px 24px rgba(20,50,120,0.14)}}
.dmc-top{{display:flex;align-items:center;gap:10px}}
.dmc-avatar{{width:48px;height:48px;border-radius:50%;background:#eef3fb;border:2px solid #c4d0e4;display:flex;align-items:center;justify-content:center;font-size:20px;color:#3b7dd8;flex-shrink:0;overflow:hidden}}
.dmc-avatar img{{width:100%;height:100%;object-fit:cover;border-radius:50%}}
.dmc-info{{flex:1;min-width:0}}
.dmc-nome{{font-size:16px;font-weight:800;color:#1a3a6b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:.2px;margin-bottom:3px}}
.dmc-filial{{font-size:13px;color:#3b7dd8;text-transform:uppercase;font-weight:700;letter-spacing:.5px;margin-bottom:2px}}
.dmc-cpf{{font-size:14px;color:#5a6e8a;font-family:monospace;letter-spacing:.8px;font-weight:600}}
.dmc-badges{{display:flex;flex-wrap:wrap;gap:5px}}
.dmc-badge{{padding:5px 12px;border-radius:4px;font-size:13px;font-weight:800;letter-spacing:.3px;display:flex;align-items:center;gap:4px}}
.dmc-badge.ok{{background:rgba(22,163,74,0.1);color:#16a34a;border:1px solid rgba(22,163,74,0.3)}}
.dmc-badge.pend{{background:rgba(217,119,6,0.1);color:#d97706;border:1px solid rgba(217,119,6,0.3)}}
.dmc-infracao{{display:flex;align-items:center;gap:10px;background:#f4f7fc;border-radius:8px;padding:10px 12px;border:1.5px solid #dde6f4}}
.dmc-inf-icon{{font-size:20px;flex-shrink:0}}
.dmc-inf-body{{flex:1;min-width:0}}
.dmc-inf-label{{font-size:9px;color:#5a6e8a;text-transform:uppercase;letter-spacing:1px;font-weight:700}}
.dmc-inf-val{{font-size:28px;font-weight:900;line-height:1;margin-top:1px}}
.dmc-inf-val.vel{{color:#dc2626}}.dmc-inf-val.mul{{color:#d97706}}.dmc-inf-val.acid{{color:#be185d}}
.kpi-empty{{grid-column:1/-1;text-align:center;padding:40px;color:#9aaabb;font-size:12px}}
.kpi-empty i{{font-size:32px;margin-bottom:10px;display:block;color:#c4d0e4}}
.empty-state{{text-align:center;padding:40px;color:#9aaabb}}
.empty-state i{{font-size:36px;margin-bottom:12px;color:#c4d0e4}}
.empty-state p{{font-size:15px}}

/* ── RESPONSIVO ── */
@media (max-width:1024px){{
  .kpi-row{{grid-template-columns:repeat(3,1fr)}}
  .filial-grid{{grid-template-columns:repeat(2,1fr)}}
  .driver-profile-grid{{grid-template-columns:1fr;padding:12px}}
  .profile-card-left{{max-width:100%}}
  .meta-grid{{grid-template-columns:repeat(2,1fr)}}
  .dss-matrix-container{{grid-template-columns:repeat(3,1fr)}}
}}

@media (max-width:768px){{
  .top-bar{{flex-wrap:wrap;gap:8px;padding:8px 10px}}
  .luft-name{{font-size:20px}}
  .pct-val{{font-size:22px}}
  .kpi-row{{grid-template-columns:repeat(2,1fr);gap:8px}}
  .kpi-val{{font-size:36px}}
  .kpi{{padding:12px 14px}}
  .content{{padding:8px 8px}}
  .panel{{padding:8px}}
  .filial-grid{{grid-template-columns:1fr}}
  .fc-count{{font-size:36px}}
  .modal-split{{grid-template-columns:1fr;grid-template-rows:auto 1fr}}
  .modal-sidebar{{flex-direction:row;flex-wrap:wrap;gap:6px}}
  .modal-kpi-card{{flex:1;min-width:120px;padding:8px}}
  .m-val{{font-size:22px}}
  .modal-box{{padding:10px;gap:8px}}
  .driver-profile-grid{{grid-template-columns:1fr;padding:8px;gap:10px}}
  .profile-details-right{{gap:8px}}
  .meta-grid{{grid-template-columns:1fr}}
  .dss-matrix-container{{grid-template-columns:repeat(2,1fr)}}
  .kpi-cards-grid{{grid-template-columns:1fr;padding:10px 12px;gap:10px}}
  .kpi-modal-overlay{{padding:4px}}
  .kpi-modal-head{{padding:10px 12px}}
  .kpi-modal-label{{font-size:13px}}
  .admin-panel-body.open{{max-height:420px}}
  .form-grid{{grid-template-columns:1fr 1fr;gap:8px}}
  .charts-row{{grid-template-columns:1fr!important}}
}}

@media (max-width:900px){{
  .charts-row{{grid-template-columns:1fr!important}}
}}

@media (max-width:480px){{
  .kpi-row{{grid-template-columns:repeat(2,1fr);gap:6px}}
  .kpi-lbl{{font-size:10px;letter-spacing:.5px}}
  .kpi-sub{{font-size:10px}}
  .luft-name{{font-size:16px}}
  .brand-logo{{padding:4px 8px}}
  .pct-box{{padding:4px 8px}}
  .pct-val{{font-size:18px}}
  .pct-lbl{{font-size:9px}}
  .modal-title{{font-size:13px}}
  .modal-sidebar{{flex-direction:column}}
  .modal-kpi-card{{min-width:unset}}
  .dss-matrix-container{{grid-template-columns:repeat(2,1fr);gap:4px}}
  .month-dss-box{{padding:5px}}
  .month-name-lbl{{font-size:10px}}
  .week-checkbox-label{{font-size:10px}}
  .form-grid{{grid-template-columns:1fr;gap:6px}}
  .m-table{{font-size:12px}}
  .m-table th,.m-table td{{padding:8px 8px}}
  .fc-name{{font-size:16px}}
  .fc-count{{font-size:28px}}
  .sbar-lbl{{font-size:11px;width:52px}}
}}
</style>
</head>
<body class="db">

<!-- SPLASH -->
<div id="splash-screen">
  <div id="splash-bg"></div>
  <div class="splash-card">
    <div class="splash-logo-txt">Gestão<span> Operacional</span></div>
    <div class="splash-sub">Sistema de Controle de Motoristas</div>

    <!-- TELA DE LOGIN -->
    <div id="loginBox">
      <div class="splash-label" style="margin-bottom:18px;"><i class="fa-solid fa-lock" style="margin-right:6px"></i>Acesso Restrito</div>
      <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:14px;">
        <input type="text" id="loginUser" placeholder="Usuário"
          style="background:rgba(255,255,255,0.08);border:1.5px solid rgba(59,125,216,0.4);color:#fff;padding:10px 14px;border-radius:8px;font-size:14px;outline:none;letter-spacing:.5px;"
           >
        <input type="password" id="loginPass" placeholder="Senha"
          style="background:rgba(255,255,255,0.08);border:1.5px solid rgba(59,125,216,0.4);color:#fff;padding:10px 14px;border-radius:8px;font-size:14px;outline:none;letter-spacing:.5px;"
          >
      </div>
       <button id="btnEntrar"
        style="width:100%;background:#3b7dd8;color:#fff;border:none;padding:11px;border-radius:8px;font-size:13px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;">
        <i class="fa-solid fa-right-to-bracket" style="margin-right:6px"></i>Entrar
      </button>
      <div id="loginErro" style="color:#ff4444;font-size:12px;margin-top:10px;min-height:16px;font-weight:600;"></div>
    </div>

    <!-- TELA DE CARREGAMENTO (oculta até login ok) -->
    <div id="loadingBox" style="display:none;">
      <div class="splash-label"><i class="fa-solid fa-database" style="margin-right:6px"></i>Conectando ao Google Sheets</div>
      <div class="splash-drop-area" style="cursor:default;pointer-events:none;margin-top:14px;">
        <div class="splash-drop-icon"><i class="fa-brands fa-google" style="color:#34a853"></i></div>
        <div class="splash-drop-txt">
          <strong>Google Sheets</strong><br>
          Carregando base de dados...
        </div>
      </div>
      <div class="splash-progress" id="splashProgress"><div class="splash-progress-bar" id="splashProgressBar"></div></div>
      <div class="splash-status" id="splashStatus">Aguardando conexão...</div>
    </div>
  </div>
</div>

<!-- Spinner global -->
<div class="spinner-overlay" id="spinnerOverlay"><div class="spinner"></div></div>

<!-- Toast global -->
<div class="toast" id="toastMsg"><i class="fa-solid fa-circle-check"></i><span id="toastText"></span></div>

<div class="top-bar">
  <div class="brand">
    <div class="brand-logo"><div class="dot-anim"></div><div class="brand-name">Controle<br><span class="brand-sub">Motoristas</span></div></div>
    <div class="luft-name">LUFT<span> LOGISTICS</span></div>
  </div>
  <div class="pct-box" style="display:flex;align-items:center;gap:16px;">
    <div>
      <div class="pct-lbl">Regularidade Geral DSS</div>
      <div class="pct-val" id="macroPctDss">—</div>
    </div>
    <button class="btn-save-master" onclick="salvarTudoNoSheets()">
      <i class="fa-solid fa-floppy-disk"></i> Salvar
    </button>
  </div>
</div>

<div class="content">

  <div class="admin-panel">
    <div class="admin-panel-header" onclick="toggleFormulario()">
      <div class="admin-panel-title"><i class="fa-solid fa-user-plus"></i> Inclusão de Condutores</div>
      <button class="btn-toggle-form" id="btnToggleForm">
        <i class="fa-solid fa-plus"></i> Novo Condutor
        <i class="fa-solid fa-chevron-down chevron"></i>
      </button>
    </div>
    <div class="admin-panel-body" id="formBody">
      <div class="form-grid">
        <div class="form-group"><label>CPF do Motorista</label><input type="text" id="addCpf" placeholder="000.000.000-00"></div>
        <div class="form-group"><label>Nome Completo</label><input type="text" id="addNome" placeholder="Nome do profissional"></div>
        <div class="form-group"><label>Filial Base</label><input type="text" id="addFilial" placeholder="Ex: BARUERI"></div>
        <div class="form-group">
          <label>Curso Reciclagem</label>
          <select id="addRec"><option value="PENDENTE">PENDENTE</option><option value="OK">OK</option></select>
        </div>
        <div class="form-group">
          <label>Sessão Simulador</label>
          <select id="addSim"><option value="PENDENTE">PENDENTE</option><option value="OK">OK</option></select>
        </div>
        <button class="btn-add" onclick="adicionarNovoMotorista()"><i class="fa-solid fa-plus"></i> Inserir Condutor</button>
      </div>
    </div>
  </div>

  <div class="kpi-row">
   <div class="kpi blue" onclick="abrirKpiModal('total')" title="Ver todos os motoristas">
      <div class="kpi-lbl">Total Motoristas</div>
      <div style="display:flex;align-items:flex-end;justify-content:space-between;">
        <div class="kpi-val" id="kpiTotal">—</div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;padding-bottom:4px;gap:1px;">
          <div style="font-size:8px;color:#1a4fa0;font-weight:700;text-transform:uppercase;letter-spacing:.5px;opacity:.8;">cadastrados</div>
          <div id="kpiTotalAnual" style="font-size:17px;font-weight:900;color:#1a4fa0;font-family:'Courier New',monospace;letter-spacing:1px;text-shadow:0 0 6px rgba(59,125,216,0.5);">—</div>
        </div>
      </div>
      <div class="kpi-sub">Todas as filiais</div>
    </div>

    <div class="kpi green" onclick="abrirKpiModal('comDss')" title="Ver motoristas com DSS ok no mês">
      <div class="kpi-lbl">Com DSS ok</div>
      <div style="display:flex;align-items:flex-end;justify-content:space-between;">
        <div class="kpi-val" id="kpiRecOk">—</div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;padding-bottom:4px;gap:1px;">
          <div style="font-size:8px;color:#16a34a;font-weight:700;text-transform:uppercase;letter-spacing:.5px;opacity:.8;">sessões/ano</div>
          <div id="kpiRecOkAnual" style="font-size:17px;font-weight:900;color:#16a34a;font-family:'Courier New',monospace;letter-spacing:1px;text-shadow:0 0 6px rgba(34,204,136,0.5);">—</div>
        </div>
      </div>
      <div class="kpi-sub" id="kpiDssSub">Mês atual — 4/4 semanas</div>
    </div>

    <div class="kpi amber" onclick="abrirKpiModal('semDss')" title="Ver motoristas pendentes no mês">
      <div class="kpi-lbl">Pendentes DSS</div>
      <div style="display:flex;align-items:flex-end;justify-content:space-between;">
        <div class="kpi-val" id="kpiSimOk">—</div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;padding-bottom:4px;gap:1px;">
          <div style="font-size:8px;color:#d97706;font-weight:700;text-transform:uppercase;letter-spacing:.5px;opacity:.8;">em falta/ano</div>
          <div id="kpiPendAnual" style="font-size:17px;font-weight:900;color:#d97706;font-family:'Courier New',monospace;letter-spacing:1px;text-shadow:0 0 6px rgba(255,170,0,0.5);">—</div>
        </div>
      </div>
      <div class="kpi-sub" id="kpiPendSub">Mês atual — menos de 4</div>
    </div>

    <div class="kpi red" onclick="abrirKpiModal('excesso')" title="Ver motoristas com excesso de velocidade">
      <div class="kpi-lbl">Excesso Velocidade</div>
      <div style="display:flex;align-items:flex-end;justify-content:space-between;">
        <div class="kpi-val" id="kpiExcesso">—</div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;padding-bottom:4px;gap:1px;">
          <div style="font-size:8px;color:#dc2626;font-weight:700;text-transform:uppercase;letter-spacing:.5px;opacity:.8;">motoristas</div>
          <div id="kpiExcessoMot" style="font-size:17px;font-weight:900;color:#dc2626;font-family:'Courier New',monospace;letter-spacing:1px;text-shadow:0 0 6px rgba(255,68,68,0.5);">—</div>
        </div>
      </div>
      <div class="kpi-sub">Total Ocorrências</div>
    </div>

    <div class="kpi red" onclick="abrirKpiModal('multas')" title="Ver motoristas com multas">
      <div class="kpi-lbl">Total Multas</div>
      <div style="display:flex;align-items:flex-end;justify-content:space-between;">
        <div class="kpi-val" id="kpiMultas">—</div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;padding-bottom:4px;gap:1px;">
          <div style="font-size:8px;color:#dc2626;font-weight:700;text-transform:uppercase;letter-spacing:.5px;opacity:.8;">motoristas</div>
          <div id="kpiMultasMot" style="font-size:17px;font-weight:900;color:#dc2626;font-family:'Courier New',monospace;letter-spacing:1px;text-shadow:0 0 6px rgba(255,68,68,0.5);">—</div>
        </div>
      </div>
      <div class="kpi-sub">Total Ocorrências</div>
    </div>

    <div class="kpi red" onclick="abrirKpiModal('acidentes')" title="Ver motoristas com acidentes">
      <div class="kpi-lbl">Total Acidentes</div>
      <div style="display:flex;align-items:flex-end;justify-content:space-between;">
        <div class="kpi-val" id="kpiAcidentes">—</div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;padding-bottom:4px;gap:1px;">
          <div style="font-size:8px;color:#dc2626;font-weight:700;text-transform:uppercase;letter-spacing:.5px;opacity:.8;">motoristas</div>
          <div id="kpiAcidentesMot" style="font-size:17px;font-weight:900;color:#dc2626;font-family:'Courier New',monospace;letter-spacing:1px;text-shadow:0 0 6px rgba(255,68,68,0.5);">—</div>
        </div>
      </div>
      <div class="kpi-sub">Total Ocorrências</div>
    </div>
  </div>

 <div style="display:grid;grid-template-columns:2fr 1fr;gap:12px;margin-bottom:12px;width:100%;min-width:0;" class="charts-row">
    <div class="panel" style="display:flex;flex-direction:column;margin-bottom:0;min-width:0;overflow:hidden;">
      <div class="sec-title">DSS por sessão — __ANO__ (registros realizados)</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:10px;align-items:center;">
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#16a34a;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#16a34a;"></span>100% adesão</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#3b7dd8;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#3b7dd8;"></span>+50% adesão</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#d97706;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#d97706;"></span>Menos de 50%</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#dc2626;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#dc2626;"></span>Sem registro</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#1a3a6b;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#1a3a6b;border:1px solid #c4d0e4;"></span>Semana atual</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#9aaabb;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:rgba(180,200,230,0.5);"></span>Futuro</span>
      </div>
      <div class="chart-wrap" id="dssChartWrap" style="height:260px;transition:height 0.4s ease;"><canvas id="dssChart"></canvas></div>
    </div>
    <div class="panel" style="display:flex;flex-direction:column;margin-bottom:0;min-width:0;overflow:hidden;">
      <div class="sec-title">Motoristas por filial — total e pendências DSS</div>
      <div class="leg">
        <div class="leg-item"><span class="leg-sq" style="background:#22cc88"></span>Com DSS</div>
        <div class="leg-item"><span class="leg-sq" style="background:#ff4444"></span>Sem DSS</div>
      </div>
      <div class="chart-wrap" style="flex:1;min-height:160px;"><canvas id="filialChart"></canvas></div>
    </div>
     <div class="panel" style="display:flex;flex-direction:column;margin-bottom:0;min-width:0;overflow:hidden;">
      <div class="sec-title">Status geral anual — indicadores por mês</div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:10px;align-items:center;">
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#16a34a;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#16a34a;"></span>100% adesão</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#3b7dd8;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#3b7dd8;"></span>+50% adesão</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#d97706;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#d97706;"></span>Menos de 50%</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#dc2626;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#dc2626;"></span>Sem registro</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#1a3a6b;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:#1a3a6b;border:1px solid #c4d0e4;"></span>Mês atual</span>
        <span style="display:flex;align-items:center;gap:5px;font-size:10px;font-weight:700;color:#9aaabb;"><span style="display:inline-block;width:22px;height:8px;border-radius:2px;background:rgba(180,200,230,0.5);"></span>Futuro</span>
      </div>
      <div style="position:relative;width:100%;flex:1;min-height:160px;"><canvas id="statusAnualChart" role="img" aria-label="Gráfico de barras com DSS realizados, acidentes, multas e excessos de velocidade por mês"></canvas></div>
    </div>
    <div class="panel" style="display:flex;flex-direction:column;margin-bottom:0;min-width:0;overflow:hidden;">
      <div class="sec-title">DSS anual por filial — sessões realizadas</div>
      <div class="leg">
        <div class="leg-item"><span class="leg-sq" style="background:#16a34a"></span>100% adesão</div>
        <div class="leg-item"><span class="leg-sq" style="background:#3b7dd8"></span>+50%</div>
        <div class="leg-item"><span class="leg-sq" style="background:#d97706"></span>&lt;50%</div>
        <div class="leg-item"><span class="leg-sq" style="background:#dc2626"></span>Sem DSS</div>
      </div>
      <div class="chart-wrap" style="flex:1;min-height:160px;"><canvas id="filialAnualChart"></canvas></div>
    </div>
  </div>
    <div style="margin-bottom:8px;display:flex;flex-wrap:wrap;gap:8px">
      <div class="leg-item"><span class="leg-sq" style="background:#22cc88"></span>Reciclagem ok</div>
      <div class="leg-item"><span class="leg-sq" style="background:#4a9eff"></span>Simulador ok</div>
      <div class="leg-item"><span class="leg-sq" style="background:#ff4444"></span>Acidentes / Multas</div>
      <div class="leg-item"><span class="leg-sq" style="background:#ffaa00"></span>Exc. velocidade</div>
    </div>
    <div class="filial-grid" id="filialGrid">
      <div class="empty-state" style="grid-column:1/-1">
        <i class="fa-solid fa-building-user"></i>
        <p>Nenhum motorista cadastrado ainda.<br>Use o formulário acima para inserir o primeiro condutor.</p>
      </div>
    </div>
  </div>
</div>

<!-- Modal KPI -->
<div class="kpi-modal-overlay" id="kpiModal">
  <div class="kpi-modal-box">
    <div class="kpi-modal-head">
      <div class="kpi-modal-head-left">
        <div class="kpi-modal-icon" id="kpiModalIcon"></div>
        <div>
          <div class="kpi-modal-label" id="kpiModalLabel">—</div>
          <div class="kpi-modal-count" id="kpiModalCount">0 motoristas</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <button id="btnBaixarPdfPendentes" style="display:none;background:transparent;color:#22cc88;border:1.5px solid #22cc88;padding:5px 14px;font-size:10px;font-weight:800;letter-spacing:1px;text-transform:uppercase;border-radius:5px;cursor:pointer;align-items:center;gap:6px;" onmouseover="this.style.color='#ff4444';this.style.borderColor='#ff4444'" onmouseout="this.style.color='#22cc88';this.style.borderColor='#22cc88'"><i class="fa-solid fa-file-pdf"></i> Baixar PDF</button>
        <button class="kpi-modal-close" onclick="fecharKpiModal()"><i class="fa-solid fa-xmark"></i></button>
      </div>
    </div>
    <div class="kpi-modal-search">
      <input type="text" id="kpiSearchInput" placeholder="🔍  Buscar por nome, CPF ou filial…" oninput="filtrarCardsKpi()">
    </div>
    <div class="kpi-mes-filtro" id="kpiMesFiltro"></div>
    <div class="kpi-cards-grid" id="kpiCardsGrid"></div>
  </div>
</div>

<!-- Modal Filial -->
<div class="modal-overlay" id="filialModal">
  <div class="modal-box">
    <div class="modal-header">
      <div class="modal-title"><i class="fa-solid fa-location-dot" style="color:#4a9eff"></i>&nbsp;Filial: <span id="mUnidadeName">...</span></div>
      <button class="btn-close" onclick="fecharJanelaFilial()"><i class="fa-solid fa-xmark"></i></button>
    </div>
    <div class="modal-split">
      <div class="modal-sidebar">
        <div class="modal-kpi-card" onclick="filtrarFilialPorIndicador('todos')"><div class="m-lbl">Total de Motoristas</div><div class="m-val" id="mTotalDrivers">0</div></div>
        <div class="modal-kpi-card" onclick="filtrarFilialPorIndicador('dss')"><div class="m-lbl">DSS Realizados (Ano)</div><div class="m-val" id="mWithDss" style="color:#22cc88">0</div></div>
        <div class="modal-kpi-card" onclick="filtrarFilialPorIndicador('reciclagem')"><div class="m-lbl">Reciclagem OK</div><div class="m-val" id="mRecOk" style="color:#16a34a">0</div></div>
        <div class="modal-kpi-card" onclick="filtrarFilialPorIndicador('simulador')"><div class="m-lbl">Simulador OK</div><div class="m-val" id="mSimOk" style="color:#3b7dd8">0</div></div>
        <div class="modal-kpi-card" onclick="filtrarFilialPorIndicador('excesso')"><div class="m-lbl">Excesso Velocidade</div><div class="m-val" id="mExcVel" style="color:#dc2626">0</div></div>
        <div class="modal-kpi-card" onclick="filtrarFilialPorIndicador('multas')"><div class="m-lbl">Total Multas</div><div class="m-val" id="mMultas" style="color:#d97706">0</div></div>
        <div class="modal-kpi-card" onclick="filtrarFilialPorIndicador('acidentes')"><div class="m-lbl">Total Acidentes</div><div class="m-val" id="mAcidentes" style="color:#dc2626">0</div></div>
      </div>
      <div class="modal-main">
        <div style="padding:10px 14px;border-bottom:1px solid #dde6f4;background:#fff;flex-shrink:0;">
          <input type="text" id="filialSearchInput" placeholder="🔍  Buscar por nome ou CPF…" oninput="filtrarTabelaFilial()" style="width:100%;background:#f4f7fc;border:1.5px solid #c4d0e4;color:#1a2a44;padding:7px 12px;border-radius:6px;font-size:13px;outline:none;">
        </div>
        <div class="table-container">
          <table class="m-table">
            <thead>
              <tr>
                <th>CPF / Motorista (Clique para abrir a ficha)</th>
                <th>Reciclagem</th><th>Simulador</th>
                <th style="text-align:center">Excesso Vel.</th>
                <th style="text-align:center">Multas</th>
                <th style="text-align:center">Acidentes</th>
              </tr>
            </thead>
            <tbody id="mDriversTableBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Modal Ficha Individual -->
<div class="modal-overlay" id="driverModal" style="z-index:10000;background:rgba(0,0,0,0.55);backdrop-filter:blur(4px);padding:0;">
  <div class="modal-box" style="max-width:none;width:100%;height:100%;border-radius:0;border:none;background:#ffffff;display:flex;flex-direction:column;">
    <div class="modal-header" style="border-color:#d0d8e8;background:#f0f4fa;flex-shrink:0;">
      <div class="modal-title" style="font-size:13px;color:#1a3a6b;"><i class="fa-solid fa-id-card" style="color:#1a7a4a"></i> <span style="color:#1a3a6b;">FICHA INDIVIDUAL DO CONDUTOR — HISTÓRICO E COMPLIANCE</span></div>
      <div style="display:flex;align-items:center;gap:8px;">
        <button id="btnConfirmarFicha" onclick="confirmarEdicaoFicha()" style="background:#1a5c2a;color:#ffffff;border:1px solid #14481f;width:auto;padding:0 16px;height:28px;border-radius:4px;font-weight:700;font-size:11px;cursor:pointer;display:flex;align-items:center;gap:6px;">
          <i class="fa-solid fa-check"></i> Confirmar Alterações
        </button>
        <button id="btnVoltarFicha" onclick="voltarPaginaAnterior()" style="display:none;background:#7a1a1a;color:#ffffff;border:1px solid #5c1212;width:auto;padding:0 14px;height:28px;border-radius:4px;font-weight:700;font-size:11px;cursor:pointer;align-items:center;gap:6px;">
          <i class="fa-solid fa-arrow-left"></i> Voltar
        </button>
        <button id="btnFecharFicha" onclick="fecharJanelaDriver()" style="background:#7a1a1a;color:#ffffff;border:1px solid #5c1212;width:28px;height:28px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;"><i class="fa-solid fa-xmark"></i></button>
      </div>
    </div>
    <div class="driver-profile-grid" id="driverProfileContent" style="flex:1;overflow-y:auto;"></div>
  </div>
</div>

<input type="file" id="hiddenPhotoInput" accept="image/*" style="display:none;" onchange="processarFotoCarregada(this)">

<script>
const ACCESS_TOKEN = '{_ACCESS_TOKEN}';
const SHEET_ID_JS  = '{SHEET_ID}';
const SHEET_NAME_JS= '{SHEET_NAME}';
const SHEETS_BASE  = 'https://sheets.googleapis.com/v4/spreadsheets';
const DADOS_INICIAIS = {json.dumps(ler_todos_motoristas(), ensure_ascii=False)};
const MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
               "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];

let motoristasDB         = DADOS_INICIAIS;
let dssChartInstance      = null;
let filialChartInstance   = null;
let filialAnualChartInst  = null;
let motoristaEmEdicaoCpf = null;
let fotoTemporariaBase64 = null;
let filialModalAtiva     = null;
let fichaOrigemModal     = null;

function mostrarSpinner(show){{ document.getElementById('spinnerOverlay').classList.toggle('show', show); }}

function toast(msg, tipo='ok'){{
  const el  = document.getElementById('toastMsg');
  const txt = document.getElementById('toastText');
  txt.textContent = msg;
  el.className = `toast ${{tipo}} show`;
  setTimeout(() => el.classList.remove('show'), 3500);
}}

function motoristasParaLinhas(lista){{
  return lista.map(m => {{
    const row = [
      m.cpf||'', m.nome||'', m.filial||'', m.telefone||'', m.email||'', m.foto||'',
      m.reciclagem||'PENDENTE', m.simulador||'PENDENTE',
      m.excesso||0, m.multas||0, m.acidentes||0,
      m.obsAcidente||'', m.obsMultas||'', m.obsGerais||'',
      m.obsReciclagem||'', m.obsSimulador||'',
      m.cnh||'', m.validadeCnh||'', m.admissao||''
    ];
    const meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                   "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];
    meses.forEach(mes => {{
      const sems = m.dssAnual?.[mes] || [false,false,false,false];
      for(let s=0;s<4;s++) row.push(sems[s] ? 1 : 0);
    }});
    return row;
  }});
}}

function _comprimirBase64(base64, maxPx, qualidade){{
  return new Promise(resolve => {{
    if(!base64 || !base64.startsWith('data:image')){{ resolve(base64 || ''); return; }}
    const img = new Image();
    img.onload = () => {{
      const canvas = document.createElement('canvas');
      const escala = Math.min(1, maxPx / Math.max(img.width, img.height));
      canvas.width  = Math.round(img.width  * escala);
      canvas.height = Math.round(img.height * escala);
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);

      // Tenta qualidade pedida, se passar de 35.000 chars reduz mais
      let resultado = canvas.toDataURL('image/jpeg', qualidade);
      if(resultado.length > 35000){{
        resultado = canvas.toDataURL('image/jpeg', 0.3);
      }}
      if(resultado.length > 35000){{
        // Última tentativa: reduz canvas para metade
        const c2 = document.createElement('canvas');
        c2.width  = Math.round(canvas.width  * 0.5);
        c2.height = Math.round(canvas.height * 0.5);
        c2.getContext('2d').drawImage(canvas, 0, 0, c2.width, c2.height);
        resultado = c2.toDataURL('image/jpeg', 0.25);
      }}
      // Se ainda assim passar, descarta a foto para não corromper o banco
      if(resultado.length > 35000){{
        resolve('');
        toast('Foto muito grande mesmo após compressão. Use uma imagem menor.', 'erro');
        return;
      }}
      resolve(resultado);
    }};
    img.onerror = () => resolve('');
    img.src = base64;
  }});
}}

async function salvarTodosNaSheetsAPI(lista){{
  const auth = `Bearer ${{ACCESS_TOKEN}}`;
  const rangeBase = `${{SHEET_NAME_JS}}!A2:ZZ`;

  // Comprime fotos antes de montar o payload — evita estourar limite da API
  const listaSegura = await Promise.all(lista.map(async m => {{
    const fotoComprimida = m.foto ? await _comprimirBase64(m.foto, 80, 0.5) : '';
    return {{ ...m, foto: fotoComprimida }};
  }}));

  // Verifica tamanho antes de qualquer operação destrutiva
  const payload = JSON.stringify({{ values: motoristasParaLinhas(listaSegura) }});
  const tamanhoMB = new Blob([payload]).size / 1024 / 1024;
  if(tamanhoMB > 8){{
    return {{ ok: false, erro: `Foto muito grande (${{tamanhoMB.toFixed(1)}} MB). Reduza a imagem.` }};
  }}

  // 1. Limpa — só executa depois que o payload foi validado
  const clearResp = await fetch(
    `${{SHEETS_BASE}}/${{SHEET_ID_JS}}/values/${{encodeURIComponent(rangeBase)}}:clear`,
    {{ method: 'POST', headers: {{ 'Authorization': auth }} }}
  );
  if(!clearResp.ok){{
    const err = await clearResp.text();
    return {{ ok: false, erro: 'Erro ao limpar planilha: ' + err }};
  }}

  if(listaSegura.length === 0) return {{ ok: true }};

  // 2. Escreve as novas linhas
  const resp = await fetch(
    `${{SHEETS_BASE}}/${{SHEET_ID_JS}}/values/${{encodeURIComponent(rangeBase)}}?valueInputOption=USER_ENTERED`,
    {{
      method: 'PUT',
      headers: {{ 'Authorization': auth, 'Content-Type': 'application/json' }},
      body: payload
    }}
  );
  if(!resp.ok){{
    const err = await resp.text();
    return {{ ok: false, erro: 'Erro ao salvar dados: ' + err }};
  }}
  return {{ ok: true }};
}}
// ── KPI Modal ──
const KPI_CONFIG = {{
  total:    {{ label:'Todos os Motoristas',         icon:'fa-users',             cor:'#7ab8ff', bg:'rgba(74,159,255,0.15)',  filtro: m => true, dssModal:true }},
  comDss:   {{ label:'Com DSS Ok',                  icon:'fa-circle-check',      cor:'#22cc88', bg:'rgba(34,204,136,0.15)', filtro: (m,mes) => dssOkNoMes(m, mes), dssModal:true }},
  semDss:   {{ label:'Pendentes DSS',               icon:'fa-clock',             cor:'#ffaa00', bg:'rgba(255,170,0,0.15)',  filtro: (m,mes) => !dssOkNoMes(m, mes), dssModal:true }},
  excesso:  {{ label:'Com Excesso de Velocidade',   icon:'fa-gauge-high',        cor:'#ff6666', bg:'rgba(255,68,68,0.15)',  filtro: m => Math.max(0, parseInt(m.excesso)   || 0) > 0 }},
  multas:   {{ label:'Com Multas Registradas',      icon:'fa-file-circle-xmark', cor:'#ff6666', bg:'rgba(255,68,68,0.15)',  filtro: m => Math.max(0, parseInt(m.multas)    || 0) > 0 }},
  acidentes:{{ label:'Com Acidentes Registrados',   icon:'fa-car-burst',         cor:'#ff6666', bg:'rgba(255,68,68,0.15)',  filtro: m => Math.max(0, parseInt(m.acidentes) || 0) > 0 }},
}};

let kpiListaAtual = [];
let kpiMesAtual   = null;
let kpiTipoAtual  = null;

function mesCorrente(){{ return MESES[new Date().getMonth()]; }}

function abrirKpiModal(tipo, mes){{
  kpiTipoAtual = tipo;
  const cfg = KPI_CONFIG[tipo];
  if(!mes) mes = cfg.dssModal ? mesCorrente() : null;
  kpiMesAtual = mes;
  _aplicarFiltroKpi();
  document.getElementById('kpiModalIcon').innerHTML  = `<i class="fa-solid ${{cfg.icon}}" style="color:${{cfg.cor}}"></i>`;
  document.getElementById('kpiModalIcon').style.background = cfg.bg;
  document.getElementById('kpiModalLabel').textContent = cfg.label + (mes ? ` — ${{mes}}` : '');
  document.getElementById('kpiSearchInput').value = '';
  const mesFiltroEl = document.getElementById('kpiMesFiltro');
  if(cfg.dssModal){{
    mesFiltroEl.classList.add('visible');
    mesFiltroEl.innerHTML = MESES.map(m => `<button class="mes-btn${{m === kpiMesAtual ? ' ativo' : ''}}" onclick="trocarMesKpi('${{m}}')">${{m.substring(0,3).toUpperCase()}}</button>`).join('');
  }} else {{
    mesFiltroEl.classList.remove('visible');
    mesFiltroEl.innerHTML = '';
  }}
  document.getElementById('kpiModal').classList.add('show');
  const btnPdf = document.getElementById('btnBaixarPdfPendentes');
  if(btnPdf){{
    if(tipo === 'semDss' || tipo === 'comDss'){{
      btnPdf.style.display = 'flex';
      btnPdf.onclick = tipo === 'semDss' ? gerarRelatorioPdfPendentes : gerarRelatorioPdfRealizados;
      btnPdf.innerHTML = '<i class="fa-solid fa-file-pdf"></i> Baixar PDF';
    }} else {{ btnPdf.style.display = 'none'; }}
  }}
}}

function trocarMesKpi(mes){{
  kpiMesAtual = mes;
  const cfg = KPI_CONFIG[kpiTipoAtual];
  document.getElementById('kpiModalLabel').textContent = cfg.label + ` — ${{mes}}`;
  document.getElementById('kpiMesFiltro').querySelectorAll('.mes-btn').forEach(b => {{
    b.classList.toggle('ativo', b.textContent === mes.substring(0,3).toUpperCase());
  }});
  _aplicarFiltroKpi();
  document.getElementById('kpiSearchInput').value = '';
}}

function _aplicarFiltroKpi(){{
  const cfg = KPI_CONFIG[kpiTipoAtual];
  kpiListaAtual = motoristasDB.filter(m => cfg.filtro(m, kpiMesAtual));
  document.getElementById('kpiModalCount').textContent = `${{kpiListaAtual.length}} motorista${{kpiListaAtual.length !== 1 ? 's' : ''}}`;
  renderizarCardsKpi(kpiListaAtual);
}}

function filtrarCardsKpi(){{
  const q = document.getElementById('kpiSearchInput').value.toLowerCase();
  const filtrados = q
    ? kpiListaAtual.filter(m => m.nome.toLowerCase().includes(q) || m.cpf.includes(q) || (m.filial||'').toLowerCase().includes(q))
    : kpiListaAtual;
  renderizarCardsKpi(filtrados);
}}

function renderizarCardsKpi(lista){{
  const grid = document.getElementById('kpiCardsGrid');
  if(lista.length === 0){{ grid.innerHTML = `<div class="kpi-empty"><i class="fa-solid fa-magnifying-glass"></i>Nenhum motorista encontrado.</div>`; return; }}
  const cfg = kpiTipoAtual ? KPI_CONFIG[kpiTipoAtual] : null;
  const isDssModal  = cfg && cfg.dssModal;
  const isExcesso   = kpiTipoAtual === 'excesso';
  const isMultas    = kpiTipoAtual === 'multas';
  const isAcidentes = kpiTipoAtual === 'acidentes';
  const isInfracao  = isExcesso || isMultas || isAcidentes;
  grid.innerHTML = lista.map(m => {{
    const avatar = m.foto ? `<img src="${{m.foto}}" alt="">` : `<i class="fa-solid fa-user-tie"></i>`;
    const nExc   = Math.max(0, parseInt(m.excesso)   || 0);
    const nMul   = Math.max(0, parseInt(m.multas)    || 0);
    const nAcid  = Math.max(0, parseInt(m.acidentes) || 0);
    if(isInfracao){{
      let infVal, infCls, infIcon, infLabel;
      if(isExcesso)   {{ infVal=nExc;  infCls='vel';  infIcon='fa-gauge-high';          infLabel='Excessos de Velocidade'; }}
      if(isMultas)    {{ infVal=nMul;  infCls='mul';  infIcon='fa-file-circle-xmark';   infLabel='Multas Registradas'; }}
      if(isAcidentes) {{ infVal=nAcid; infCls='acid'; infIcon='fa-car-burst';            infLabel='Acidentes Registrados'; }}
      return `<div class="driver-mini-card" onclick="irParaFichaViaKpi('${{m.cpf}}')" title="Abrir ficha de ${{m.nome}}">
        <div class="dmc-top"><div class="dmc-avatar">${{avatar}}</div><div class="dmc-info"><div class="dmc-nome">${{m.nome}}</div><div class="dmc-filial">${{m.filial||'—'}}</div></div></div>
        <div class="dmc-cpf">${{m.cpf}}</div>
        <div class="dmc-infracao"><i class="fa-solid ${{infIcon}} dmc-inf-icon" style="color:${{infCls==='vel'?'#ff4444':infCls==='mul'?'#ff6622':'#ff4488'}}"></i>
          <div class="dmc-inf-body"><div class="dmc-inf-label">${{infLabel}}</div><div class="dmc-inf-val ${{infCls}}">${{infVal}}</div></div>
        </div></div>`;
    }}
    let semanasHtml = '';
    if(isDssModal && kpiMesAtual){{
      const sems = dssDoMes(m, kpiMesAtual);
      semanasHtml = `<div class="dmc-semanas">` +
        sems.map((ok,i) => `<div class="dmc-sem"><span class="dmc-sem-lbl">${{i+1}}ª S</span><span class="dmc-sem-dot ${{ok?'ok':'pend'}}">${{ok?'✓':'✗'}}</span></div>`).join('') +
        `</div>`;
    }}
    const nDssMes  = isDssModal && kpiMesAtual ? contarDssMes(m, kpiMesAtual) : contarDssSessoes(m);
    const dssOkMes = isDssModal && kpiMesAtual ? dssOkNoMes(m, kpiMesAtual)   : temDss(m);
    const mesLabel = kpiMesAtual ? kpiMesAtual.substring(0,3).toUpperCase() : '';
    const badges = [
      isDssModal
        ? (dssOkMes
            ? `<span class="dmc-badge ok"><i class="fa-solid fa-calendar-check"></i> ${{mesLabel}} ${{nDssMes}}/4 ✓</span>`
            : `<span class="dmc-badge pend"><i class="fa-solid fa-clock"></i> ${{mesLabel}} ${{nDssMes}}/4 pendente</span>`)
        : (temDss(m) ? `<span class="dmc-badge ok">DSS ok</span>` : `<span class="dmc-badge pend">Sem DSS</span>`)
    ].join('');
    const cardClass = dssOkMes ? 'card-ok' : 'card-pend';
    return `<div class="driver-mini-card ${{cardClass}}" onclick="irParaFichaViaKpi('${{m.cpf}}')" title="Abrir ficha de ${{m.nome}}">
      <div class="dmc-top"><div class="dmc-avatar">${{avatar}}</div><div class="dmc-info"><div class="dmc-nome">${{m.nome}}</div><div class="dmc-filial">${{m.filial||'—'}}</div></div></div>
      <div class="dmc-cpf">${{m.cpf}}</div>
      ${{semanasHtml}}<div class="dmc-badges">${{badges}}</div></div>`;
  }}).join('');
}}

function irParaFichaViaKpi(cpf){{ fichaOrigemModal='kpi'; fecharKpiModal(); setTimeout(()=>abrirFichaMotorista(cpf),120); }}
function fecharKpiModal(){{ document.getElementById('kpiModal').classList.remove('show'); }}
document.addEventListener('click', e => {{ if(e.target === document.getElementById('kpiModal')) fecharKpiModal(); }});

function toggleFormulario(){{
  const body = document.getElementById('formBody');
  const btn  = document.getElementById('btnToggleForm');
  const aberto = body.classList.toggle('open');
  btn.classList.toggle('open', aberto);
}}

async function carregarDados(){{
  mostrarSpinner(true);
  try{{
    const res = await apiFetch('/api/motoristas');
    if(res.ok){{ motoristasDB = res.motoristas; atualizarDashboardCompleto(); }}
    else {{ toast('Erro ao carregar dados: ' + res.erro, 'erro'); }}
  }} catch(e){{ toast('Falha de conexão com o servidor.', 'erro'); }}
  finally{{ mostrarSpinner(false); }}
}}

function gerarMatrizDssEmBranco(){{
  const d = {{}};
  MESES.forEach(m => {{ d[m] = [false,false,false,false]; }});
  return d;
}}

function temDss(m){{ return MESES.some(mes => m.dssAnual[mes] && m.dssAnual[mes].some(s => s)); }}
function contarDssSessoes(m){{ let t=0; MESES.forEach(mes=>{{ if(m.dssAnual[mes]) m.dssAnual[mes].forEach(s=>{{ if(s) t++; }}); }}); return t; }}
function dssDoMes(m, mes){{ return m.dssAnual && m.dssAnual[mes] ? m.dssAnual[mes] : [false,false,false,false]; }}
function contarDssMes(m, mes){{ return dssDoMes(m, mes).filter(Boolean).length; }}
function dssOkNoMes(m, mes){{ return contarDssMes(m, mes) >= 4; }}

function agruparPorFilial(){{
  const mapa = {{}};
  motoristasDB.forEach(m => {{
    const f = (m.filial||'').toUpperCase().trim() || 'SEM FILIAL';
    if(!mapa[f]) mapa[f] = {{ name:f, total:0, comDss:0, recOk:0, simOk:0, acid:0, multas:0, excVel:0 }};
    mapa[f].total++;
    if(temDss(m)) mapa[f].comDss++;
    if(m.reciclagem === 'OK') mapa[f].recOk++;
    if(m.simulador  === 'OK') mapa[f].simOk++;
    mapa[f].acid   += Math.max(0, parseInt(m.acidentes || 0));
    mapa[f].multas += Math.max(0, parseInt(m.multas    || 0));
    mapa[f].excVel += Math.max(0, parseInt(m.excesso   || 0));
  }});
  return Object.values(mapa).sort((a,b) => b.total - a.total);
}}

function atualizarDashboardCompleto(){{
  const filiais    = agruparPorFilial();
  const totalM     = motoristasDB.length;
  const _mesDash   = MESES[new Date().getMonth()];
  const totalComDss= motoristasDB.filter(m => dssOkNoMes(m, _mesDash)).length;
  const totalPend  = totalM - totalComDss;
  const totalExc   = motoristasDB.reduce((acc,m) => acc + Math.max(0, parseInt(m.excesso)   || 0), 0);
  const totalMul   = motoristasDB.reduce((acc,m) => acc + Math.max(0, parseInt(m.multas)    || 0), 0);
  const totalAcid  = motoristasDB.reduce((acc,m) => acc + Math.max(0, parseInt(m.acidentes) || 0), 0);
  document.getElementById('kpiTotal').textContent    = totalM;
  document.getElementById('kpiRecOk').textContent    = totalComDss;
  document.getElementById('kpiSimOk').textContent    = totalPend;
  document.getElementById('kpiExcesso').textContent  = totalExc;
  document.getElementById('kpiMultas').textContent   = totalMul;
  document.getElementById('kpiAcidentes').textContent= totalAcid;
  const pct = totalM > 0 ? ((totalComDss / totalM)*100).toFixed(1) + '%' : '—';
  const _mesLabel = _mesDash.substring(0,3).toUpperCase();
  const subDss  = document.getElementById('kpiDssSub');
  const subPend = document.getElementById('kpiPendSub');
  if(subDss)  subDss.textContent  = _mesLabel + ' — 4/4 semanas';
  if(subPend) subPend.textContent = _mesLabel + ' — menos de 4';
  document.getElementById('macroPctDss').textContent = pct;

  const totalDssAnual = motoristasDB.reduce((acc, m) => {{
    MESES.forEach(mes => {{
      if(m.dssAnual && m.dssAnual[mes]) acc += m.dssAnual[mes].filter(Boolean).length;
    }});
    return acc;
  }}, 0);
  const totalSessoesAnual = totalM * MESES.length * 4;
  const motExcesso = motoristasDB.filter(m => Math.max(0,parseInt(m.excesso)||0) > 0).length;
  const motMultas  = motoristasDB.filter(m => Math.max(0,parseInt(m.multas)||0)  > 0).length;
  const motAcident = motoristasDB.filter(m => Math.max(0,parseInt(m.acidentes)||0) > 0).length;
  const _s = (id,v) => {{ const e=document.getElementById(id); if(e) e.textContent=v; }};
  _s('kpiTotalAnual',   totalM);
  _s('kpiRecOkAnual',   totalDssAnual);
  _s('kpiPendAnual',    totalSessoesAnual - totalDssAnual);
  _s('kpiExcessoMot',   motExcesso);
  _s('kpiMultasMot',    motMultas);
  _s('kpiAcidentesMot', motAcident);

  renderizarGridFiliais(filiais);
  renderizarGraficos(filiais);
}}

function renderizarGridFiliais(filiais){{
  const filColors = ['#1a4fa0','#16a34a','#d97706','#dc2626','#7c3aed','#be185d','#0e7490','#9a3412','#166534','#1e40af','#9d174d','#0369a1'];
  const grid = document.getElementById('filialGrid');
  if(filiais.length === 0){{ grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><i class="fa-solid fa-building-user"></i><p>Nenhum motorista cadastrado ainda.<br>Use o formulário acima para inserir o primeiro condutor.</p></div>`; return; }}
  grid.innerHTML = '';
  filiais.forEach((f, i) => {{
    const color  = filColors[i % filColors.length];
    const pSem   = f.total > 0 ? Math.round((f.total - f.comDss)/ f.total *100) : 100;
    const recPct = f.total > 0 ? Math.round(f.recOk / f.total *100) : 0;
    const simPct = f.total > 0 ? Math.round(f.simOk / f.total *100) : 0;
    const acidPct= f.total > 0 ? Math.round(f.acid  / f.total *100) : 0;
    const multPct= f.total > 0 ? Math.round(f.multas/ f.total *100) : 0;
    const velPct = f.total > 0 ? Math.round(f.excVel/ f.total *100) : 0;
    grid.innerHTML += `<div class="fc">
      <div class="fc-name">${{f.name}}</div>
      <div class="fc-count" style="color:${{color}}">${{f.total}}</div>
      <div class="situation-bars">
        <div class="sbar ok"><span class="sbar-lbl">Recicl</span><div class="sbar-track"><div class="sbar-fill" style="width:${{recPct}}%;background:#16a34a"></div></div><span class="sbar-cnt" style="color:#16a34a">${{f.recOk}}</span></div>
        <div class="sbar ok"><span class="sbar-lbl">Simul</span><div class="sbar-track"><div class="sbar-fill" style="width:${{simPct}}%;background:#3b7dd8"></div></div><span class="sbar-cnt" style="color:#3b7dd8">${{f.simOk}}</span></div>
        <div class="sbar neg"><span class="sbar-lbl">Acid</span><div class="sbar-track"><div class="sbar-fill" style="width:${{acidPct}}%;background:#dc2626"></div></div><span class="sbar-cnt">${{f.acid}}</span></div>
        <div class="sbar neg"><span class="sbar-lbl">Multas</span><div class="sbar-track"><div class="sbar-fill" style="width:${{multPct}}%;background:#dc2626"></div></div><span class="sbar-cnt">${{f.multas}}</span></div>
        <div class="sbar pend"><span class="sbar-lbl">Vel</span><div class="sbar-track"><div class="sbar-fill" style="width:${{velPct}}%;background:#d97706"></div></div><span class="sbar-cnt" style="color:#d97706">${{f.excVel}}</span></div>
        <div class="sbar pend"><span class="sbar-lbl">DSS</span><div class="sbar-track" style="background:#dc2626;position:relative;overflow:hidden;"><div class="sbar-fill" style="width:${{f.total>0?Math.round(f.comDss/f.total*100):0}}%;background:#16a34a;position:absolute;left:0;top:0;height:100%;border-radius:3px;transition:width .3s;"></div></div><span class="sbar-cnt" style="color:${{f.comDss===f.total&&f.total>0?'#16a34a':'#dc2626'}};width:auto;min-width:36px;">${{f.comDss}}/${{f.total}}</span></div>
      </div>
      <button class="btn-zoom" onclick="expandirFilial('${{f.name}}')"><i class="fa-solid fa-maximize"></i> Ver Condutores</button>
    </div>`;
  }});
}}

function renderizarGraficos(filiais){{
  if(dssChartInstance)      dssChartInstance.destroy();
  if(filialChartInstance)   filialChartInstance.destroy();
  if(filialAnualChartInst)  filialAnualChartInst.destroy();
  const now         = new Date();
  const mesAtualIdx = now.getMonth();
  const semAtualIdx = Math.min(3, Math.floor((now.getDate() - 1) / 7));
  const monthsShort = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
  const dssLabels=[], dssData=[], dssBarColors=[], dssBorderColors=[];
  monthsShort.forEach((m, mi) => {{
    [0,1,2,3].forEach(wi => {{
      dssLabels.push(`${{wi+1}}ª ${{m}}`);
      const mesFull = MESES[mi];
      const count = motoristasDB.filter(mot => mot.dssAnual && mot.dssAnual[mesFull] && mot.dssAnual[mesFull][wi]).length;
      const isCurrent = mi === mesAtualIdx && wi === semAtualIdx;
      const isPast    = !isCurrent && (mi < mesAtualIdx || (mi === mesAtualIdx && wi <= semAtualIdx));
      dssData.push(count);
      if(isCurrent) {{ dssBarColors.push('#1a3a6b'); dssBorderColors.push('#1a3a6b'); }}
      else if(isPast) {{
        const total = motoristasDB.length;
        const pct   = total > 0 ? count / total : 0;
        if(pct >= 1.0)      {{ dssBarColors.push('#16a34a'); dssBorderColors.push('#16a34a'); }}
        else if(pct >= 0.5) {{ dssBarColors.push('#3b7dd8'); dssBorderColors.push('#3b7dd8'); }}
        else if(pct >  0)   {{ dssBarColors.push('#d97706'); dssBorderColors.push('#d97706'); }}
        else                {{ dssBarColors.push('#dc2626'); dssBorderColors.push('#dc2626'); }}
      }} else {{ dssBarColors.push('rgba(180,200,230,0.4)'); dssBorderColors.push('rgba(180,200,230,0.6)'); }}
    }});
  }});
  const maxVal = Math.max(...dssData, 1);
  const dynamicH = Math.min(500, Math.max(260, 160 + maxVal * 4));
  const wrap = document.getElementById('dssChartWrap');
  if(wrap) wrap.style.height = dynamicH + 'px';
  const yStep = maxVal <= 5 ? 1 : maxVal <= 20 ? 2 : maxVal <= 50 ? 5 : maxVal <= 100 ? 10 : Math.ceil(maxVal / 10);
  // Dataset de fundo: vermelho fino para semanas passadas sem registro
  const dssDataFundo = dssData.map((v, i) => {{
    const mi = Math.floor(i / 4);
    const wi = i % 4;
    const isCur = mi === mesAtualIdx && wi === semAtualIdx;
    const isPas = !isCur && (mi < mesAtualIdx || (mi === mesAtualIdx && wi <= semAtualIdx));
    return (isPas && v === 0) ? 1 : 0;
  }});
  const dssFundoCores = dssData.map((v, i) => {{
    const mi = Math.floor(i / 4);
    const wi = i % 4;
    const isCur = mi === mesAtualIdx && wi === semAtualIdx;
    const isPas = !isCur && (mi < mesAtualIdx || (mi === mesAtualIdx && wi <= semAtualIdx));
    return (isPas && v === 0) ? 'rgba(220,38,38,0.25)' : 'transparent';
  }});

  dssChartInstance = new Chart(document.getElementById('dssChart'), {{
    type:'bar',
    data:{{ labels:dssLabels, datasets:[
      {{ label:'Fundo Sem Registro', data:dssDataFundo, backgroundColor:dssFundoCores, borderColor:dssFundoCores, borderWidth:0, borderRadius:4, borderSkipped:false }},
      {{ label:'Sessões DSS', data:dssData.slice(), backgroundColor:dssBarColors, borderColor:dssBorderColors, borderWidth:1, borderRadius:4, borderSkipped:false }}
    ]}},
    options:{{
      responsive:true, maintainAspectRatio:false,
      animation:{{ duration:600, easing:'easeOutQuart' }},
      plugins:{{ legend:{{ display:false }},
        tooltip:{{
          callbacks:{{
            title: items => {{ const i=items[0].dataIndex; const mi=Math.floor(i/4); const wi=i%4; return `${{wi+1}}ª semana — ${{MESES[mi]}}`; }},
            label: ctx => {{
              const i=ctx.dataIndex; const mi=Math.floor(i/4); const wi=i%4;
              const isFut = mi > mesAtualIdx || (mi === mesAtualIdx && wi > semAtualIdx);
              if(isFut) return ' Ainda não realizado';
              const real=dssData[i]; const total=motoristasDB.length;
              const pct=total>0?Math.round(real/total*100):0;
              return [` ${{real}} de ${{total}} motorista${{total!==1?'s':''}}`, ` Adesão: ${{pct}}%`];
            }}
          }},
          backgroundColor:'#ffffff',borderColor:'#dde6f4',borderWidth:1,
          titleColor:'#1a3a6b',bodyColor:'#5a6e8a',padding:10,cornerRadius:6
        }}
      }},
      scales:{{
        x:{{ ticks:{{ color:'#5a6e8a',font:{{ size:9 }},maxRotation:45,autoSkip:false, callback(val,i){{ const mi=Math.floor(i/4);const wi=i%4;const isCur=mi===mesAtualIdx&&wi===semAtualIdx;return isCur?'▶ '+this.getLabelForValue(val):this.getLabelForValue(val); }} }},grid:{{ color:'rgba(180,200,230,0.4)' }} }},
        y:{{ ticks:{{ color:'#5a6e8a',font:{{ size:10 }},stepSize:yStep,callback:v=>Number.isInteger(v)?v:'' }},grid:{{ color:'rgba(180,200,230,0.4)' }},min:0,max:Math.ceil(maxVal*1.15)||1 }}
      }}
    }}
  }});
 filialChartInstance = new Chart(document.getElementById('filialChart'), {{
    type:'bar',
    data:{{ labels:filiais.map(f=>f.name), datasets:[
      {{ label:'Com DSS',  data:filiais.map(f=>f.comDss),          backgroundColor:'#16a34a', borderRadius:3, borderSkipped:false }},
      {{ label:'Sem DSS',  data:filiais.map(f=>f.total-f.comDss),  backgroundColor:'rgba(220,38,38,0.12)', borderColor:'rgba(220,38,38,0.3)', borderWidth:1, borderRadius:3, borderSkipped:false }}
    ]}},
    options:{{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{ display:false }} }},
      scales:{{
        x:{{ stacked:true, ticks:{{ color:'#5a6e8a',font:{{ size:8 }},maxRotation:30,autoSkip:false }},grid:{{ color:'rgba(180,200,230,0.4)' }} }},
        y:{{ stacked:true, ticks:{{ color:'#5a6e8a',font:{{ size:9 }} }},grid:{{ color:'rgba(180,200,230,0.4)' }},min:0 }}
      }}
    }}
  }});

  if(window._statusAnualChartInstance) window._statusAnualChartInstance.destroy();
  const statusLabels   = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
  const mesAtualIdxS   = new Date().getMonth();
  const totalMotS      = motoristasDB.length;
  const statusDssMes   = MESES.map(mes => {{
    let n = 0;
    motoristasDB.forEach(m => {{ if(dssOkNoMes(m, mes)) n++; }});
    return n;
  }});
  const statusBarCors  = MESES.map((mes, mi) => {{
    const pct     = totalMotS > 0 ? statusDssMes[mi] / totalMotS : 0;
    const isCur   = mi === mesAtualIdxS;
    const isPast  = mi < mesAtualIdxS;
    if(isCur)           return '#1a3a6b';
    if(!isPast)         return 'rgba(180,200,230,0.4)';
    if(pct >= 1.0)      return '#16a34a';
    if(pct >= 0.5)      return '#3b7dd8';
    if(pct >  0)        return '#d97706';
    return '#dc2626';
  }});
  const statusBordCors = MESES.map((mes, mi) => {{
    const pct     = totalMotS > 0 ? statusDssMes[mi] / totalMotS : 0;
    const isCur   = mi === mesAtualIdxS;
    const isPast  = mi < mesAtualIdxS;
    if(isCur)           return '#1a3a6b';
    if(!isPast)         return 'rgba(180,200,230,0.6)';
    if(pct >= 1.0)      return '#16a34a';
    if(pct >= 0.5)      return '#3b7dd8';
    if(pct >  0)        return '#d97706';
    return '#dc2626';
  }});
  const statusFundoCores = MESES.map((mes, mi) => {{
    const isCur  = mi === mesAtualIdxS;
    const isPast = mi < mesAtualIdxS;
    return (isPast && !isCur && statusDssMes[mi] === 0) ? 'rgba(220,38,38,0.25)' : 'transparent';
  }});
  const statusDataFundo = MESES.map((mes, mi) => {{
    const isCur  = mi === mesAtualIdxS;
    const isPast = mi < mesAtualIdxS;
    return (isPast && !isCur && statusDssMes[mi] === 0) ? 1 : 0;
  }});
 // ── Gráfico DSS Anual por Filial ──
  const filialAnualLabels = filiais.map(f => f.name);
  const filialAnualDss    = filiais.map(f => {{
    let total = 0;
    motoristasDB.filter(m => (m.filial||'').toUpperCase() === f.name).forEach(m => {{
      MESES.forEach(mes => {{ if(m.dssAnual && m.dssAnual[mes]) total += m.dssAnual[mes].filter(Boolean).length; }});
    }});
    return total;
  }});
  const filialAnualMax = filiais.map(f => f.total * MESES.length * 4);
  const filialAnualFalta = filiais.map((f, i) => Math.max(0, filialAnualMax[i] - filialAnualDss[i]));
  const filialAnualBarCors = filiais.map((f, i) => {{
    const pct = filialAnualMax[i] > 0 ? filialAnualDss[i] / filialAnualMax[i] : 0;
    if(pct >= 1.0)      return '#16a34a';
    if(pct >= 0.5)      return '#3b7dd8';
    if(pct >  0)        return '#d97706';
    return '#dc2626';
  }});
  filialAnualChartInst = new Chart(document.getElementById('filialAnualChart'), {{
    type: 'bar',
    data: {{ labels: filialAnualLabels, datasets: [
      {{ label: 'Sessões realizadas', data: filialAnualDss,   backgroundColor: filialAnualBarCors, borderRadius: 3, borderSkipped: false }},
      {{ label: 'Sessões em falta',   data: filialAnualFalta, backgroundColor: 'rgba(220,38,38,0.12)', borderColor: 'rgba(220,38,38,0.3)', borderWidth: 1, borderRadius: 3, borderSkipped: false }}
    ]}},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            title: items => items[0].label,
            label: ctx => {{
              const i     = ctx.dataIndex;
              const real  = filialAnualDss[i];
              const maxi  = filialAnualMax[i];
              const pct   = maxi > 0 ? Math.round(real / maxi * 100) : 0;
              return [` ${{real}} sessões realizadas de ${{maxi}}`, ` Adesão anual: ${{pct}}%`];
            }}
          }},
          backgroundColor:'#ffffff', borderColor:'#dde6f4', borderWidth:1,
          titleColor:'#1a3a6b', bodyColor:'#5a6e8a', padding:10, cornerRadius:6
        }}
      }},
      scales: {{
        x: {{ stacked: true, ticks: {{ color:'#5a6e8a', font:{{ size:8 }}, maxRotation:30, autoSkip:false }}, grid: {{ color:'rgba(180,200,230,0.4)' }} }},
        y: {{ stacked: true, ticks: {{ color:'#5a6e8a', font:{{ size:9 }}, callback: v => Number.isInteger(v) ? v : '' }}, grid: {{ color:'rgba(180,200,230,0.4)' }}, min: 0 }}
      }}
    }}
  }});

  window._statusAnualChartInstance = new Chart(document.getElementById('statusAnualChart'), {{
    type:'bar',
    data:{{ labels:statusLabels, datasets:[
      {{ label:'Fundo Sem Registro', data:statusDataFundo, backgroundColor:statusFundoCores, borderColor:statusFundoCores, borderWidth:0, borderRadius:4, borderSkipped:false }},
      {{ label:'DSS ok no mês', data:statusDssMes, backgroundColor:statusBarCors, borderColor:statusBordCors, borderWidth:1, borderRadius:4, borderSkipped:false }}
    ]}},
    options:{{
      responsive:true, maintainAspectRatio:false,
      animation:{{ duration:600, easing:'easeOutQuart' }},
      plugins:{{ legend:{{ display:false }},
        tooltip:{{
          callbacks:{{
            title: items => statusLabels[items[0].dataIndex] + ' ' + new Date().getFullYear(),
            label: ctx => {{
              const mi = ctx.dataIndex;
              const count = statusDssMes[mi];
              const total = totalMotS;
              const pct = total > 0 ? Math.round(count/total*100) : 0;
              if(mi > mesAtualIdxS) return ' Ainda não realizado';
              return [` ${{count}} de ${{total}} motorista${{total!==1?'s':''}}`, ` Adesão: ${{pct}}%`];
            }}
          }},
          backgroundColor:'#ffffff',borderColor:'#dde6f4',borderWidth:1,
          titleColor:'#1a3a6b',bodyColor:'#5a6e8a',padding:10,cornerRadius:6
        }}
      }},
      scales:{{
        x:{{ ticks:{{ color:'#5a6e8a',font:{{size:10}} }},grid:{{ color:'rgba(180,200,230,0.4)' }} }},
        y:{{ ticks:{{ color:'#5a6e8a',font:{{size:10}},stepSize:1,callback:v=>Number.isInteger(v)?v:'' }},grid:{{ color:'rgba(180,200,230,0.4)' }},min:0 }}
      }}
    }}
  }});
}}

async function adicionarNovoMotorista(){{
  const cpf    = document.getElementById('addCpf').value.trim();
  const nome   = document.getElementById('addNome').value.toUpperCase().trim();
  const filial = document.getElementById('addFilial').value.toUpperCase().trim();
  if(!cpf || !nome || !filial){{ toast('Preencha CPF, Nome e Filial.', 'erro'); return; }}
  const novo = {{
    cpf, nome, filial, telefone:'', email:'', foto:'',
    reciclagem: document.getElementById('addRec').value,
    simulador:  document.getElementById('addSim').value,
    excesso:0, multas:0, acidentes:0,
    obsAcidente:'', obsMultas:'', obsGerais:'', obsReciclagem:'', obsSimulador:'',
    cnh:'', validadeCnh:'', admissao:'',
    dssAnual: gerarMatrizDssEmBranco()
  }};
  mostrarSpinner(true);
  try{{
    motoristasDB.push(novo);
    const res = await salvarTodosNaSheetsAPI(motoristasDB);
    if(res.ok){{
      document.getElementById('addCpf').value = '';
      document.getElementById('addNome').value = '';
      document.getElementById('addFilial').value = '';
      document.getElementById('formBody').classList.remove('open');
      document.getElementById('btnToggleForm').classList.remove('open');
      atualizarDashboardCompleto();
      toast('Condutor inserido e salvo no Google Sheets!');
    }} else {{
      motoristasDB.pop();
      toast(res.erro || 'Erro ao inserir.', 'erro');
    }}
  }} catch(e){{ toast('Falha de conexão: ' + e.message, 'erro'); }}
  finally{{ mostrarSpinner(false); }}
}}

function expandirFilial(nomeFilial){{
  filialModalAtiva = nomeFilial;
  document.getElementById('mUnidadeName').textContent = nomeFilial;
  const listagem = motoristasDB.filter(m => (m.filial||'').toUpperCase() === nomeFilial.toUpperCase());
  document.getElementById('mTotalDrivers').textContent = listagem.length;
  const totalDss = listagem.reduce((acc,m) => acc + contarDssSessoes(m), 0);
  document.getElementById('mWithDss').textContent = totalDss;
  document.getElementById('mRecOk').textContent = listagem.filter(m => m.reciclagem === 'OK').length;
  document.getElementById('mSimOk').textContent = listagem.filter(m => m.simulador === 'OK').length;
  document.getElementById('mExcVel').textContent = listagem.reduce((acc,m) => acc + Math.max(0, parseInt(m.excesso)||0), 0);
  document.getElementById('mMultas').textContent = listagem.reduce((acc,m) => acc + Math.max(0, parseInt(m.multas)||0), 0);
  document.getElementById('mAcidentes').textContent = listagem.reduce((acc,m) => acc + Math.max(0, parseInt(m.acidentes)||0), 0);
  const tbody = document.getElementById('mDriversTableBody');
  tbody.innerHTML = '';
  if(listagem.length === 0){{
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:#666;">Nenhum motorista cadastrado nesta filial.</td></tr>';
  }} else {{
    listagem.forEach(m => {{
      tbody.innerHTML += `<tr class="driver-row" onclick="abrirFichaMotorista('${{m.cpf}}')">
        <td><div class="m-name">${{m.nome}}</div><div class="m-cpf">CPF: ${{m.cpf}}</div></td>
        <td><span class="m-badge ${{m.reciclagem==='OK'?'ok':'pend'}}">${{m.reciclagem}}</span></td>
        <td><span class="m-badge ${{m.simulador==='OK'?'ok':'pend'}}">${{m.simulador}}</span></td>
        <td style="text-align:center"><span class="m-count-badge">${{m.excesso}}</span></td>
        <td style="text-align:center"><span class="m-count-badge">${{m.multas}}</span></td>
        <td style="text-align:center"><span class="m-count-badge">${{m.acidentes}}</span></td>
      </tr>`;
    }});
  }}
  document.getElementById('filialModal').style.display = 'flex';
}}

function fecharJanelaFilial(){{ document.getElementById('filialModal').style.display = 'none'; }}
function filtrarTabelaFilial(){{
  const q = document.getElementById('filialSearchInput').value.toLowerCase();
  document.querySelectorAll('#mDriversTableBody tr').forEach(tr => {{
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
function filtrarFilialPorIndicador(tipo){{
  document.querySelectorAll('#mDriversTableBody tr').forEach(tr => {{
    tr.style.display = '';
  }});
  document.getElementById('filialSearchInput').value = '';
  const listagem = motoristasDB.filter(m => (m.filial||'').toUpperCase() === (filialModalAtiva||'').toUpperCase());
  const filtrados = listagem.filter(m => {{
   if(tipo==='todos')     return true;
    if(tipo==='dss')       return contarDssSessoes(m) > 0;
    if(tipo==='reciclagem') return m.reciclagem === 'OK';
    if(tipo==='simulador') return m.simulador === 'OK';
    if(tipo==='excesso')   return Math.max(0,parseInt(m.excesso)||0)   > 0;
    if(tipo==='multas')    return Math.max(0,parseInt(m.multas)||0)    > 0;
    if(tipo==='acidentes') return Math.max(0,parseInt(m.acidentes)||0) > 0;
    return true;
  }});
  const cpfsFiltrados = new Set(filtrados.map(m => m.cpf));
  document.querySelectorAll('#mDriversTableBody tr').forEach(tr => {{
    const cpfCell = tr.querySelector('.m-cpf');
    if(cpfCell){{
      const cpf = cpfCell.textContent.replace('CPF: ','').trim();
      tr.style.display = cpfsFiltrados.has(cpf) ? '' : 'none';
    }}
  }});
}}
function filtrarTabelaFilial(){{
  const q = document.getElementById('filialSearchInput').value.toLowerCase();
  document.querySelectorAll('#mDriversTableBody tr').forEach(tr => {{
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}

function abrirFichaMotorista(cpf){{
  const m = motoristasDB.find(x => x.cpf === cpf);
  if(!m) return;
  motoristaEmEdicaoCpf = cpf;
  fotoTemporariaBase64 = m.foto || null;
  const avatarHtml = m.foto
    ? `<img src="${{m.foto}}" id="profilePreviewImg">`
    : `<i class="fa-solid fa-user-tie" id="profileIconPlaceholder" style="font-size:32px;color:#4a9eff;"></i><img src="" id="profilePreviewImg" style="display:none">`;
  let matrizHtml = '';
  MESES.forEach(mes => {{
    const semanas = m.dssAnual[mes] || [false,false,false,false];
    matrizHtml += `<div class="month-dss-box">
      <div class="month-name-lbl">${{mes}}</div>
      <div class="weeks-flex">
        ${{[0,1,2,3].map(i => `<label class="week-checkbox-label"><span>${{i+1}}ªS</span><input type="checkbox" id="dss-${{mes}}-${{i}}" ${{semanas[i]?'checked':''}}></label>`).join('')}}
      </div></div>`;
  }});
  const esc = s => (s||'').replace(/"/g,'&quot;');
  let highlightSeg='', highlightDss='', badgeSegHtml='', badgeDssHtml='';
  if(fichaOrigemModal === 'kpi'){{
    if(kpiTipoAtual==='excesso')  {{ highlightSeg=' card-highlight-vel';  badgeSegHtml='<span style="margin-left:auto;font-size:8px;font-weight:800;background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;padding:2px 8px;border-radius:20px;"><i class=\\"fa-solid fa-gauge-high\\" style=\\"margin-right:3px\\"></i>Excesso de Velocidade</span>'; }}
    if(kpiTipoAtual==='multas')   {{ highlightSeg=' card-highlight-mul';  badgeSegHtml='<span style="margin-left:auto;font-size:8px;font-weight:800;background:#fff3e0;color:#c2410c;border:1px solid #fbbf7a;padding:2px 8px;border-radius:20px;"><i class=\\"fa-solid fa-file-circle-xmark\\" style=\\"margin-right:3px\\"></i>Multas</span>'; }}
    if(kpiTipoAtual==='acidentes'){{ highlightSeg=' card-highlight-acid'; badgeSegHtml='<span style="margin-left:auto;font-size:8px;font-weight:800;background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;padding:2px 8px;border-radius:20px;"><i class=\\"fa-solid fa-car-burst\\" style=\\"margin-right:3px\\"></i>Acidentes</span>'; }}
    if(kpiTipoAtual==='comDss')   {{ highlightDss=' card-highlight-dss';  badgeDssHtml='<span style="margin-left:auto;font-size:8px;font-weight:800;background:#dcfce7;color:#15803d;border:1px solid #86efac;padding:2px 8px;border-radius:20px;"><i class=\\"fa-solid fa-circle-check\\" style=\\"margin-right:3px\\"></i>DSS Ok</span>'; }}
    if(kpiTipoAtual==='semDss')   {{ highlightDss=' card-highlight-dss';  badgeDssHtml='<span style="margin-left:auto;font-size:8px;font-weight:800;background:#fef9c3;color:#a16207;border:1px solid #fde68a;padding:2px 8px;border-radius:20px;"><i class=\\"fa-solid fa-clock\\" style=\\"margin-right:3px\\"></i>Pendente DSS</span>'; }}
  }}
  document.getElementById('driverProfileContent').innerHTML = `
    <div class="profile-card-left card-condutor">
      <span class="card-stripe"></span>
      <div class="profile-card-left-body">
        <div>
          <div class="avatar-wrapper" onclick="dispararUploadFoto()">${{avatarHtml}}<div class="upload-hint">Alterar Foto</div></div>
          <div class="form-group" style="width:100%;margin-top:15px;"><label>Nome do Condutor</label><input type="text" id="editNome" value="${{esc(m.nome)}}"></div>
          <div class="form-group" style="width:100%;margin-top:10px;"><label>Filial Base</label><input type="text" id="editFilial" value="${{esc(m.filial)}}"></div>
          <div style="display:flex;flex-direction:column;gap:8px;margin-top:16px;">
            <div style="background:#fff5f5;border:1.5px solid #fca5a5;border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:12px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;"><i class="fa-solid fa-car-burst" style="color:#dc2626;margin-right:6px"></i>Acidentes</span>
              <span style="font-size:32px;font-weight:900;color:#dc2626;line-height:1;">${{m.acidentes||0}}</span>
            </div>
            <div style="background:#fffbeb;border:1.5px solid #fde68a;border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:12px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;"><i class="fa-solid fa-file-circle-xmark" style="color:#d97706;margin-right:6px"></i>Multas</span>
              <span style="font-size:32px;font-weight:900;color:#d97706;line-height:1;">${{m.multas||0}}</span>
            </div>
            <div style="background:#fffbeb;border:1.5px solid #fed7aa;border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:12px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;"><i class="fa-solid fa-gauge-high" style="color:#ea580c;margin-right:6px"></i>Exc. Velocidade</span>
              <span style="font-size:32px;font-weight:900;color:#ea580c;line-height:1;">${{m.excesso||0}}</span>
            </div>
            <div style="background:${{m.reciclagem==='OK'?'#f0fef4':'#fff5f5'}};border:1.5px solid ${{m.reciclagem==='OK'?'#86efac':'#fca5a5'}};border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:12px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;"><i class="fa-solid fa-recycle" style="color:${{m.reciclagem==='OK'?'#16a34a':'#dc2626'}};margin-right:6px"></i>Reciclagem</span>
              <span style="font-size:18px;font-weight:900;color:${{m.reciclagem==='OK'?'#16a34a':'#dc2626'}};line-height:1;">${{m.reciclagem}}</span>
            </div>
            <div style="background:${{m.simulador==='OK'?'#f0fef4':'#fff5f5'}};border:1.5px solid ${{m.simulador==='OK'?'#86efac':'#fca5a5'}};border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:12px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;"><i class="fa-solid fa-car-side" style="color:${{m.simulador==='OK'?'#16a34a':'#dc2626'}};margin-right:6px"></i>Simulador</span>
              <span style="font-size:18px;font-weight:900;color:${{m.simulador==='OK'?'#16a34a':'#dc2626'}};line-height:1;">${{m.simulador}}</span>
            </div>
          </div>
        </div>
        <button onclick="gerarFichaPdf('${{m.cpf}}')" style="background:#fff0f8;color:#1a4fa0;border:1px solid #b0c8e8;padding:8px;border-radius:7px;font-size:10px;font-weight:700;text-transform:uppercase;cursor:pointer;margin-top:6px;display:flex;align-items:center;justify-content:center;gap:6px;width:100%;transition:.18s;" onmouseover="this.style.background='#1a4fa0';this.style.color='#fff'" onmouseout="this.style.background='#fff0f8';this.style.color='#1a4fa0'">
          <i class="fa-solid fa-file-pdf"></i> Baixar Ficha em PDF
        </button>
        <button class="btn-delete-driver" onclick="deletarMotoristaAtual('${{m.cpf}}','${{esc(m.nome)}}')">
          <i class="fa-solid fa-trash-can"></i> Excluir Condutor permanentemente
        </button>
      </div>
    </div>
    <div class="profile-details-right">
      <div class="info-section-box card-contato">
        <span class="card-stripe"></span>
        <div class="card-body">
          <div class="info-block-title"><i class="fa-solid fa-phone"></i> Dados de Contato</div>
          <div class="meta-grid">
            <div class="meta-item"><label>Telefone / WhatsApp</label><input type="text" id="editTelefone" value="${{esc(m.telefone)}}" placeholder="(00) 00000-0000"></div>
            <div class="meta-item"><label>E-mail Corporativo</label><input type="email" id="editEmail" value="${{esc(m.email)}}" placeholder="nome@luft.com.br"></div>
          </div>
        </div>
      </div>
      <div class="info-section-box card-docs">
        <span class="card-stripe"></span>
        <div class="card-body">
          <div class="info-block-title"><i class="fa-solid fa-address-card"></i> Documentação</div>
          <div class="meta-grid">
            <div class="meta-item"><label>Nº Registro CNH</label><input type="text" id="editCnh" value="${{esc(m.cnh)}}"></div>
            <div class="meta-item"><label>Validade CNH</label><input type="date" id="editValidadeCnh" value="${{esc(m.validadeCnh)}}"></div>
            <div class="meta-item"><label>Data Admissão</label><input type="date" id="editAdmissao" value="${{esc(m.admissao)}}"></div>
          </div>
        </div>
      </div>
      <div class="info-section-box card-seguranca${{highlightSeg}}">
        <span class="card-stripe"></span>
        <div class="card-body">
          <div class="info-block-title"><i class="fa-solid fa-shield-halved"></i> Indicadores de Segurança & Observações${{badgeSegHtml}}</div>
          <div class="meta-grid" style="margin-bottom:12px;">
            <div class="meta-item">
              <label>Acidentes (Qtd)</label><input type="number" id="editAcidentes" value="${{m.acidentes||0}}">
              <input type="text" id="editObsAcidente" class="obs-input" style="margin-top:4px;" value="${{esc(m.obsAcidente)}}" placeholder="Obs de Acidente">
            </div>
            <div class="meta-item">
              <label>Multas (Qtd)</label><input type="number" id="editMultas" value="${{m.multas||0}}">
              <input type="text" id="editObsMultas" class="obs-input" style="margin-top:4px;" value="${{esc(m.obsMultas)}}" placeholder="Obs de Multas">
            </div>
            <div class="meta-item">
              <label>Excesso de Velocidade</label><input type="number" id="editExcesso" value="${{m.excesso||0}}">
              <input type="text" id="editObsGerais" class="obs-input" style="margin-top:4px;" value="${{esc(m.obsGerais)}}" placeholder="Obs de Excesso">
            </div>
          </div>
          <div class="meta-grid" style="border-top:1px dashed #e0d0b8;padding-top:10px;">
            <div class="meta-item">
              <label>Simulador SEST SENAT</label>
              <select id="editSimulador" style="margin-bottom:4px;">
                <option value="PENDENTE" ${{m.simulador==='PENDENTE'?'selected':''}}>PENDENTE</option>
                <option value="OK" ${{m.simulador==='OK'?'selected':''}}>OK</option>
              </select>
              <input type="text" id="editObsSimulador" class="obs-input" value="${{esc(m.obsSimulador)}}" placeholder="Obs do Simulador">
            </div>
            <div class="meta-item">
              <label>Reciclagem</label>
              <select id="editReciclagem" style="margin-bottom:4px;">
                <option value="PENDENTE" ${{m.reciclagem==='PENDENTE'?'selected':''}}>PENDENTE</option>
                <option value="OK" ${{m.reciclagem==='OK'?'selected':''}}>OK</option>
              </select>
              <input type="text" id="editObsReciclagem" class="obs-input" value="${{esc(m.obsReciclagem)}}" placeholder="Obs de Reciclagem">
            </div>
          </div>
        </div>
      </div>
      <div class="info-section-box card-dss${{highlightDss}}">
        <span class="card-stripe"></span>
        <div class="card-body">
          <div class="info-block-title"><i class="fa-solid fa-calendar-check"></i> Matriz de Controle Semanal DSS (Ano Vigente)${{badgeDssHtml}}</div>
          <div class="dss-matrix-container">${{matrizHtml}}</div>
        </div>
      </div>
    </div>`;
  document.getElementById('driverModal').style.display = 'flex';
  const btnVoltar = document.getElementById('btnVoltarFicha');
  if(fichaOrigemModal){{ btnVoltar.style.display = 'flex'; }} else {{ btnVoltar.style.display = 'none'; }}
}}

function dispararUploadFoto(){{ document.getElementById('hiddenPhotoInput').click(); }}
function processarFotoCarregada(input){{
  if(input.files && input.files[0]){{
    const reader = new FileReader();
    reader.onload = async e => {{
      // Comprime já na leitura — nunca guarda base64 gigante na memória
      fotoTemporariaBase64 = await _comprimirBase64(e.target.result, 80, 0.5);
      const img  = document.getElementById('profilePreviewImg');
      const icon = document.getElementById('profileIconPlaceholder');
      if(icon) icon.style.display = 'none';
      img.src = fotoTemporariaBase64;
      img.style.display = 'block';
    }};
    reader.readAsDataURL(input.files[0]);
  }}
}}

async function confirmarEdicaoFicha(){{
  const idx = motoristasDB.findIndex(x => x.cpf === motoristaEmEdicaoCpf);
  if(idx === -1) return;
  const dssAnual = {{}};
  MESES.forEach(mes => {{
    dssAnual[mes] = [0,1,2,3].map(i => {{
      const chk = document.getElementById(`dss-${{mes}}-${{i}}`);
      return chk ? chk.checked : false;
    }});
  }});
  const atualizado = {{
    ...motoristasDB[idx],
    nome:          document.getElementById('editNome').value.toUpperCase(),
    filial:        document.getElementById('editFilial').value.toUpperCase(),
    telefone:      document.getElementById('editTelefone').value,
    email:         document.getElementById('editEmail').value,
    cnh:           document.getElementById('editCnh').value,
    validadeCnh:   document.getElementById('editValidadeCnh').value,
    admissao:      document.getElementById('editAdmissao').value,
    reciclagem:    document.getElementById('editReciclagem').value,
    simulador:     document.getElementById('editSimulador').value,
    acidentes:     parseInt(document.getElementById('editAcidentes').value)||0,
    multas:        parseInt(document.getElementById('editMultas').value)||0,
    excesso:       parseInt(document.getElementById('editExcesso').value)||0,
    obsAcidente:   document.getElementById('editObsAcidente').value,
    obsMultas:     document.getElementById('editObsMultas').value,
    obsGerais:     document.getElementById('editObsGerais').value,
    obsReciclagem: document.getElementById('editObsReciclagem').value,
    obsSimulador:  document.getElementById('editObsSimulador').value,
    foto:          fotoTemporariaBase64 || '',
    dssAnual
  }};
  mostrarSpinner(true);
  try{{
    const anterior = motoristasDB[idx];
    motoristasDB[idx] = atualizado;
    const res = await salvarTodosNaSheetsAPI(motoristasDB);
    if(res.ok){{
      fecharJanelaDriver();
      atualizarDashboardCompleto();
      if(filialModalAtiva) expandirFilial(filialModalAtiva);
      toast('Ficha atualizada e salva no Google Sheets!');
    }} else {{
      motoristasDB[idx] = anterior;
      toast(res.erro || 'Erro ao salvar.', 'erro');
    }}
  }} catch(e){{ toast('Falha de conexão: ' + e.message, 'erro'); }}
  finally{{ mostrarSpinner(false); }}
}}

async function deletarMotoristaAtual(cpf, nome){{
  if(!confirm(`Remover permanentemente o condutor ${{nome}}?`)) return;
 mostrarSpinner(true);
  try{{
    const anterior = [...motoristasDB];
    motoristasDB = motoristasDB.filter(m => m.cpf !== cpf);
    const res = await salvarTodosNaSheetsAPI(motoristasDB);
    if(res.ok){{
      fecharJanelaDriver();
      atualizarDashboardCompleto();
      if(filialModalAtiva) expandirFilial(filialModalAtiva);
      toast('Condutor removido.');
    }} else {{
      motoristasDB = anterior;
      toast(res.erro || 'Erro ao remover.', 'erro');
    }}
  }} catch(e){{ toast('Falha de conexão: ' + e.message, 'erro'); }}
  finally{{ mostrarSpinner(false); }}
}}

async function salvarTudoNoSheets(){{
  mostrarSpinner(true);
  try{{
    const res = await salvarTodosNaSheetsAPI(motoristasDB);
    if(res.ok) toast('Base salva com sucesso no Google Sheets!');
    else toast(res.erro || 'Erro ao salvar.', 'erro');
  }} catch(e){{ toast('Falha de conexão: ' + e.message, 'erro'); }}
  finally{{ mostrarSpinner(false); }}
}}

function voltarPaginaAnterior(){{
  const origem = fichaOrigemModal;
  fecharJanelaDriver();
  if(origem === 'kpi'){{ setTimeout(() => document.getElementById('kpiModal').classList.add('show'), 80); }}
}}

function fecharJanelaDriver(){{
  document.getElementById('driverModal').style.display = 'none';
  motoristaEmEdicaoCpf = null;
  fotoTemporariaBase64 = null;
  fichaOrigemModal     = null;
  document.getElementById('btnVoltarFicha').style.display = 'none';
}}

// ── Ficha Individual PDF ──
function gerarFichaPdf(cpf){{
  const m = motoristasDB.find(x => x.cpf === cpf);
  if(!m) return;
  const now    = new Date();
  const dtStr  = now.toLocaleDateString('pt-BR');
  const hrStr  = now.toLocaleTimeString('pt-BR', {{hour:'2-digit', minute:'2-digit'}});
  const esc    = s => (s||'—').replace(/</g,'&lt;');
  const fotoHtml = m.foto
    ? `<img src="${{m.foto}}" style="width:100px;height:100px;object-fit:cover;border-radius:6px;border:2px solid #c4d0e4;">`
    : `<div style="width:100px;height:100px;border-radius:6px;border:2px dashed #c4d0e4;display:flex;align-items:center;justify-content:center;background:#f0f4fa;color:#9aaabb;font-size:11px;text-align:center;">Sem<br>Foto</div>`;

  const dssLinhas = Object.entries(m.dssAnual||{{}}).map(([mes, sems])=>{{
    const boxes = sems.map((ok,i)=>`<td style="text-align:center;padding:4px;border:1px solid #dde6f4;background:${{ok?'#dcfce7':'#fff5f5'}};color:${{ok?'#16a34a':'#dc2626'}};font-weight:800;font-size:11px;">${{ok?'✓':'✗'}}</td>`).join('');
    return `<tr><td style="padding:4px 8px;border:1px solid #dde6f4;font-size:11px;font-weight:700;color:#1a3a6b;">${{mes}}</td>${{boxes}}</tr>`;
  }}).join('');

  const html = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>LUFT LOGISTICS — Ficha | ${{m.nome}}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#fff;color:#1a2a44;padding:28px 32px;font-size:12px}}
  .header{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid #1a3a6b;padding-bottom:12px;margin-bottom:16px}}
  .brand-title{{font-size:20px;font-weight:900;color:#1a3a6b}}
  .brand-title span{{color:#22cc88}}
  .brand-sub{{font-size:10px;color:#5a6e8a;letter-spacing:1px;text-transform:uppercase;margin-top:3px}}
  .doc-info{{text-align:right;font-size:10px;color:#5a6e8a}}
  .doc-info strong{{display:block;font-size:13px;color:#1a3a6b;font-weight:800}}
  .section{{border:1.5px solid #dde6f4;border-radius:8px;margin-bottom:14px;overflow:hidden}}
  .section-head{{background:#1a3a6b;color:#fff;font-size:10px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;padding:6px 12px}}
  .section-body{{padding:12px}}
  .profile-row{{display:flex;gap:18px;align-items:flex-start}}
  .info-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;flex:1}}
  .info-item label{{font-size:9px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;display:block;margin-bottom:2px}}
  .info-item span{{font-size:13px;font-weight:700;color:#1a2a44}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:800}}
  .badge-ok{{background:#dcfce7;color:#16a34a;border:1px solid #86efac}}
  .badge-pend{{background:#fef9c3;color:#d97706;border:1px solid #fde68a}}
  .badge-red{{background:#fee2e2;color:#dc2626;border:1px solid #fca5a5}}
  .kpi-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
  .kpi-box{{border-radius:6px;padding:10px 12px;text-align:center;border:1.5px solid}}
  .kpi-box label{{font-size:9px;text-transform:uppercase;font-weight:700;letter-spacing:.5px;display:block;margin-bottom:4px}}
  .kpi-box span{{font-size:26px;font-weight:900;line-height:1}}
  .kpi-acid{{border-color:#fca5a5;background:#fff5f5}}.kpi-acid span{{color:#dc2626}}
  .kpi-mul{{border-color:#fde68a;background:#fffbeb}}.kpi-mul span{{color:#d97706}}
  .kpi-vel{{border-color:#fed7aa;background:#fff7ed}}.kpi-vel span{{color:#ea580c}}
  table.dss{{width:100%;border-collapse:collapse}}
  table.dss th{{background:#eef3fb;color:#1a4fa0;font-size:10px;font-weight:800;text-transform:uppercase;padding:5px 8px;border:1px solid #dde6f4;text-align:center}}
  .assinatura-row{{display:flex;gap:32px;margin-top:10px;align-items:flex-end}}
  .assinatura-box{{flex:1}}
  .assinatura-box .lbl{{font-size:8px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;margin-bottom:20px;display:block}}
  .assinatura-box .linha{{border:none;border-bottom:1.5px solid #1a3a6b;margin-bottom:5px}}
  .assinatura-box .sublbl{{font-size:8px;color:#1a3a6b;font-weight:700}}
  .footer{{border-top:1px solid #dde6f4;margin-top:10px;padding-top:6px;display:flex;justify-content:space-between;font-size:8px;color:#9aaabb}}
  @media print{{body{{padding:10px 16px}} .no-print{{display:none}} .section{{margin-bottom:8px}} .section-body{{padding:8px 10px}} .kpi-row{{gap:6px}} .kpi-box{{padding:6px 8px}} .kpi-box span{{font-size:20px}} table.dss td,table.dss th{{padding:3px 6px;font-size:10px}}}}
</style></head>
<body>

<div class="header">
  <div>
    <div class="brand-title">LUFT<span style="color:#22cc88"> LOGISTICS</span></div>
    <div class="brand-sub" style="color:#1a3a6b;font-weight:700;font-size:11px;margin-top:2px;letter-spacing:.5px;">Sistema de Controle de Motoristas</div>
    <div class="brand-sub">Ficha Individual do Condutor — Histórico & Compliance</div>
  </div>
  <div class="doc-info">
    <strong>Ficha do Condutor</strong>
    Emitido em: ${{dtStr}} às ${{hrStr}}<br>
    CPF: ${{esc(m.cpf)}}
  </div>
</div>

<!-- IDENTIFICAÇÃO -->
<div class="section">
  <div class="section-head">👤 Identificação do Condutor</div>
  <div class="section-body">
    <div class="profile-row">
      <div style="flex-shrink:0">${{fotoHtml}}</div>
      <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:10px 24px;">
        <div class="info-item" style="grid-column:1/-1;border-bottom:1px solid #e8eef8;padding-bottom:8px;margin-bottom:4px;">
          <label>Nome Completo</label>
          <span style="font-size:17px;font-weight:900;color:#1a3a6b;">${{esc(m.nome)}}</span>
        </div>
        <div class="info-item"><label>CPF</label><span style="font-family:monospace">${{esc(m.cpf)}}</span></div>
        <div class="info-item"><label>Filial</label><span>${{esc(m.filial)}}</span></div>
        <div class="info-item"><label>Admissão</label><span>${{m.admissao ? new Date(m.admissao+'T00:00:00').toLocaleDateString('pt-BR') : '—'}}</span></div>
        <div class="info-item"><label>Telefone</label><span>${{esc(m.telefone)}}</span></div>
        <div class="info-item"><label>E-mail</label><span>${{esc(m.email)}}</span></div>
        <div class="info-item"><label>CNH Nº</label><span style="font-family:monospace">${{esc(m.cnh)}}</span></div>
        <div class="info-item"><label>Validade CNH</label><span>${{m.validadeCnh ? new Date(m.validadeCnh+'T00:00:00').toLocaleDateString('pt-BR') : '—'}}</span></div>
        <div class="info-item" style="grid-column:1/-1;display:flex;gap:20px;padding-top:6px;border-top:1px solid #e8eef8;margin-top:2px;">
          <div style="display:flex;flex-direction:column;gap:2px;">
            <label>Reciclagem</label>
            <span class="badge ${{m.reciclagem==='OK'?'badge-ok':'badge-pend'}}">${{m.reciclagem}}</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:2px;">
            <label>Simulador</label>
            <span class="badge ${{m.simulador==='OK'?'badge-ok':'badge-pend'}}">${{m.simulador}}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- INDICADORES -->
<div class="section">
  <div class="section-head"><i>🛡</i> Indicadores de Segurança</div>
  <div class="section-body">
    <div class="kpi-row">
      <div class="kpi-box kpi-acid"><label>Acidentes</label><span>${{m.acidentes||0}}</span></div>
      <div class="kpi-box kpi-mul"><label>Multas</label><span>${{m.multas||0}}</span></div>
      <div class="kpi-box kpi-vel"><label>Exc. Velocidade</label><span>${{m.excesso||0}}</span></div>
    </div>
    ${{(m.obsAcidente||m.obsMultas||m.obsGerais||m.obsReciclagem||m.obsSimulador) ? `
    <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      ${{m.obsAcidente ? `<div style="background:#fff5f5;border:1px solid #fca5a5;border-radius:5px;padding:7px 10px;"><span style="font-size:9px;color:#dc2626;font-weight:700;text-transform:uppercase;">Obs. Acidentes</span><p style="font-size:11px;margin-top:3px;color:#1a2a44;">${{esc(m.obsAcidente)}}</p></div>` : ''}}
      ${{m.obsMultas  ? `<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:5px;padding:7px 10px;"><span style="font-size:9px;color:#d97706;font-weight:700;text-transform:uppercase;">Obs. Multas</span><p style="font-size:11px;margin-top:3px;color:#1a2a44;">${{esc(m.obsMultas)}}</p></div>` : ''}}
      ${{m.obsGerais  ? `<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:5px;padding:7px 10px;"><span style="font-size:9px;color:#ea580c;font-weight:700;text-transform:uppercase;">Obs. Velocidade</span><p style="font-size:11px;margin-top:3px;color:#1a2a44;">${{esc(m.obsGerais)}}</p></div>` : ''}}
      ${{m.obsReciclagem ? `<div style="background:#f0fef4;border:1px solid #86efac;border-radius:5px;padding:7px 10px;"><span style="font-size:9px;color:#16a34a;font-weight:700;text-transform:uppercase;">Obs. Reciclagem</span><p style="font-size:11px;margin-top:3px;color:#1a2a44;">${{esc(m.obsReciclagem)}}</p></div>` : ''}}
      ${{m.obsSimulador ? `<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:5px;padding:7px 10px;"><span style="font-size:9px;color:#1a4fa0;font-weight:700;text-transform:uppercase;">Obs. Simulador</span><p style="font-size:11px;margin-top:3px;color:#1a2a44;">${{esc(m.obsSimulador)}}</p></div>` : ''}}
    </div>` : ''}}
  </div>
</div>

<!-- DSS -->
<div class="section">
  <div class="section-head"><i>📅</i> Controle Semanal DSS — Ano Vigente</div>
  <div class="section-body">
    <table class="dss">
      <thead><tr><th style="text-align:left;padding:5px 8px;">Mês</th><th>1ª Sem</th><th>2ª Sem</th><th>3ª Sem</th><th>4ª Sem</th></tr></thead>
      <tbody>${{dssLinhas}}</tbody>
    </table>
  </div>
</div>

<!-- ASSINATURA -->
<div style="border:1.5px solid #dde6f4;border-radius:8px;margin-bottom:14px;overflow:hidden;">
  <div style="background:#1a3a6b;color:#fff;font-size:10px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;padding:6px 12px;">✍ Declaração e Assinatura</div>
  <div style="padding:14px 16px;">
    <p style="font-size:9px;color:#5a6e8a;margin-bottom:16px;line-height:1.6;font-style:italic;border-left:3px solid #1a3a6b;padding-left:8px;">
      Declaro que as informações contidas nesta ficha estão corretas e que estou ciente das normas de segurança e conformidade operacional da empresa.
    </p>
    <div style="display:flex;gap:32px;align-items:flex-end;margin-top:10px;">
      <div style="flex:2;display:flex;flex-direction:column;">
        <span style="font-size:8px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;margin-bottom:28px;display:block;">Assinatura do Condutor</span>
        <div style="border-bottom:1.5px solid #1a3a6b;margin-bottom:5px;"></div>
        <div style="font-size:9px;font-weight:700;color:#1a3a6b;">${{esc(m.nome)}}</div>
        <div style="font-size:8px;color:#5a6e8a;">CPF: ${{esc(m.cpf)}}</div>
      </div>
      <div style="flex:1;display:flex;flex-direction:column;">
        <span style="font-size:8px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;margin-bottom:28px;display:block;">Data</span>
        <div style="border-bottom:1.5px solid #1a3a6b;margin-bottom:5px;"></div>
        
      </div>
      <div style="flex:1;display:flex;flex-direction:column;">
        <span style="font-size:8px;color:#5a6e8a;text-transform:uppercase;font-weight:700;letter-spacing:.5px;margin-bottom:28px;display:block;">Local / Filial</span>
        <div style="border-bottom:1.5px solid #1a3a6b;margin-bottom:5px;"></div>
      </div>
    </div>
  </div>
</div>

<div class="footer">
  <span><strong style="color:#1a3a6b;">LUFT LOGISTICS</strong> — Sistema de Controle de Motoristas</span>
  <span>Documento gerado em ${{dtStr}} às ${{hrStr}}</span>
</div>

</body></html>`;

  const blob = new Blob([html], {{type:'text/html;charset=utf-8'}});
  const url  = URL.createObjectURL(blob);
  const win  = window.open(url, '_blank');
  if(win) win.onload = () => {{ win.focus(); win.print(); }};
}}

// ── Relatório PDF Pendentes ──
function gerarRelatorioPdfPendentes(){{
  const mes   = kpiMesAtual || mesCorrente();
  const lista = motoristasDB.filter(m => !dssOkNoMes(m, mes));
  _gerarRelatorio(mes, lista, false);
}}
function gerarRelatorioPdfRealizados(){{
  const mes   = kpiMesAtual || mesCorrente();
  const lista = motoristasDB.filter(m => dssOkNoMes(m, mes));
  _gerarRelatorio(mes, lista, true);
}}
function _gerarRelatorio(mes, lista, realizado){{
  const total = motoristasDB.length;
  const now   = new Date();
  const dtStr = now.toLocaleDateString('pt-BR') + ' ' + now.toLocaleTimeString('pt-BR',{{hour:'2-digit',minute:'2-digit'}});
  const semanas = ['1ª Sem','2ª Sem','3ª Sem','4ª Sem'];
  const porFilial = {{}};
  lista.forEach(m => {{
    const f = m.filial || 'SEM FILIAL';
    if(!porFilial[f]) porFilial[f] = [];
    porFilial[f].push(m);
  }});
  const filialKeys = Object.keys(porFilial).sort();
  let linhas = '';
  let globalIdx = 0;
  const headerColor = realizado ? '#1a5c2a' : '#1a3a5c';
  filialKeys.forEach(filial => {{
    linhas += `<tr><td colspan="8" style="background:${{headerColor}};color:#fff;font-size:10px;font-weight:800;padding:7px 12px;letter-spacing:1px;text-transform:uppercase;">${{filial}} — ${{porFilial[filial].length}} ${{realizado?'realizado':'pendente'}}${{porFilial[filial].length!==1?'s':''}}</td></tr>`;
    porFilial[filial].forEach(m => {{
      const zebra = globalIdx++ % 2 === 0 ? '#ffffff' : (realizado ? '#f2fff6' : '#f4f8ff');
      const dssMes = m.dssAnual?.[mes] || [false,false,false,false];
      const caixas = semanas.map((s,i) => {{
        const feito = dssMes[i];
        return `<td style="text-align:center;padding:6px 4px;vertical-align:middle;border-bottom:1px solid #e0e8f0;background:${{zebra}};"><div style="width:16px;height:16px;border:2px solid ${{feito?'#22aa66':'#aaaaaa'}};border-radius:3px;margin:0 auto;display:flex;align-items:center;justify-content:center;background:${{feito?'#e8fff4':'#fff'}};">${{feito?'<span style=\\"color:#22aa66;font-size:12px;font-weight:900;line-height:1;\\">✕</span>':''}}</div></td>`;
      }}).join('');
      const recOk = m.reciclagem==='OK'; const simOk = m.simulador==='OK';
      const recBox = `<div style="display:inline-flex;align-items:center;gap:4px;"><div style="width:14px;height:14px;border:2px solid ${{recOk?'#22aa66':'#aaa'}};border-radius:2px;display:flex;align-items:center;justify-content:center;background:${{recOk?'#e8fff4':'#fff'}}">${{recOk?'<span style=\\"color:#22aa66;font-size:11px;font-weight:900;\\">✕</span>':''}}</div><span style="font-size:9px;color:${{recOk?'#22aa66':'#cc4444'}};font-weight:700;">${{recOk?'OK':'Pend'}}</span></div>`;
      const simBox = `<div style="display:inline-flex;align-items:center;gap:4px;"><div style="width:14px;height:14px;border:2px solid ${{simOk?'#22aa66':'#aaa'}};border-radius:2px;display:flex;align-items:center;justify-content:center;background:${{simOk?'#e8fff4':'#fff'}}">${{simOk?'<span style=\\"color:#22aa66;font-size:11px;font-weight:900;\\">✕</span>':''}}</div><span style="font-size:9px;color:${{simOk?'#22aa66':'#cc4444'}};font-weight:700;">${{simOk?'OK':'Pend'}}</span></div>`;
      linhas += `<tr style="background:${{zebra}};"><td style="padding:6px 10px;font-size:10px;font-weight:700;color:#111;border-bottom:1px solid #e0e8f0;background:${{zebra}};">${{m.nome}}</td><td style="padding:6px 8px;font-size:9px;color:#555;font-family:monospace;border-bottom:1px solid #e0e8f0;background:${{zebra}};">${{m.cpf}}</td>${{caixas}}<td style="padding:6px 8px;border-bottom:1px solid #e0e8f0;background:${{zebra}};">${{recBox}}</td><td style="padding:6px 8px;border-bottom:1px solid #e0e8f0;background:${{zebra}};">${{simBox}}</td></tr>`;
    }});
  }});
  const titulo = realizado ? 'DSS Realizados' : 'Pendentes DSS';
  const html = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Relatório ${{titulo}} — ${{mes}} ${{now.getFullYear()}}</title>
  <style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Segoe UI',Arial,sans-serif;background:#fff;color:#111;padding:32px 28px}}
  .header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:28px;border-bottom:3px solid #1a3a5c;padding-bottom:16px}}
  .brand-title{{font-size:22px;font-weight:900;color:#1a3a5c}}.brand-title span{{color:#e85c00}}
  .brand-sub{{font-size:11px;color:#666;letter-spacing:1px;text-transform:uppercase;margin-top:4px}}
  .report-tag{{font-size:13px;font-weight:800;color:${{realizado?'#22aa66':'#cc4444'}};text-transform:uppercase;letter-spacing:1px}}
  .report-mes{{font-size:18px;font-weight:900;color:#1a3a5c;margin:2px 0}}.report-dt{{font-size:10px;color:#888}}
  .summary-box{{display:flex;gap:20px;margin-bottom:24px}}
  .s-card{{background:#f4f8ff;border:1px solid #d0dff0;border-radius:8px;padding:12px 20px;text-align:center;flex:1}}
  .s-card .s-val{{font-size:28px;font-weight:900;color:#1a3a5c}}.s-card .s-lbl{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-top:2px}}
  table{{width:100%;border-collapse:collapse;font-size:10px}}
  thead tr{{background:#1a3a5c}}thead th{{color:#fff;font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;padding:8px 10px;text-align:left}}
  thead th.center{{text-align:center}}
  .footer{{margin-top:28px;border-top:1px solid #dde;padding-top:10px;font-size:9px;color:#aaa;display:flex;justify-content:space-between}}</style></head><body>
  <div class="header"><div><div class="brand-title">LUFT<span> LOGISTICS</span></div><div class="brand-sub">Controle de Motoristas — DSS</div></div>
  <div style="text-align:right"><div class="report-tag">${{realizado?'✓ DSS Realizados':'⚠ Pendentes DSS'}}</div><div class="report-mes">${{mes.toUpperCase()}} ${{now.getFullYear()}}</div><div class="report-dt">Gerado em ${{dtStr}}</div></div></div>
  <div class="summary-box">
    <div class="s-card"><div class="s-val">${{total}}</div><div class="s-lbl">Total de Motoristas</div></div>
    <div class="s-card"><div class="s-val" style="color:#22aa66">${{motoristasDB.filter(m=>dssOkNoMes(m,mes)).length}}</div><div class="s-lbl">DSS Realizados</div></div>
    <div class="s-card"><div class="s-val" style="color:${{realizado?'#22aa66':'#cc4444'}}">${{lista.length}}</div><div class="s-lbl">${{realizado?'Realizaram no Mês':'Pendentes no Mês'}}</div></div>
    <div class="s-card"><div class="s-val" style="color:#1a3a5c">${{filialKeys.length}}</div><div class="s-lbl">Filiais</div></div>
  </div>
  <table><thead><tr><th>Motorista</th><th>CPF</th><th class="center">1ª Sem</th><th class="center">2ª Sem</th><th class="center">3ª Sem</th><th class="center">4ª Sem</th><th class="center">Reciclagem</th><th class="center">Simulador</th></tr></thead><tbody>${{linhas}}</tbody></table>
  <div class="footer"><span>LUFT Logistics — Sistema de Controle de Motoristas</span><span>Relatório ${{titulo}} • ${{mes}} ${{now.getFullYear()}}</span></div>
  </body></html>`;
  const blob = new Blob([html],{{type:'text/html;charset=utf-8'}});
  const url  = URL.createObjectURL(blob);
  const win  = window.open(url,'_blank');
  if(win) win.onload = () => {{ win.focus(); win.print(); }};
}}

// ── Login + Inicialização ──
const CREDENCIAIS = {{ usuario: 'luft123', senha: 'luft321' }};

function tentarLogin(){{
  const u = document.getElementById('loginUser').value.trim();
  const p = document.getElementById('loginPass').value.trim();
  const erro = document.getElementById('loginErro');
  if(u === CREDENCIAIS.usuario && p === CREDENCIAIS.senha){{
    document.getElementById('loginBox').style.display  = 'none';
    document.getElementById('loadingBox').style.display = 'block';
    inicializar();
  }} else {{
    erro.textContent = 'Usuário ou senha incorretos.';
    document.getElementById('loginPass').value = '';
    document.getElementById('loginPass').focus();
    setTimeout(() => {{ erro.textContent = ''; }}, 3000);
  }}
}}

(function(){{
  setTimeout(() => {{ document.getElementById('loginUser').focus(); }}, 200);

  document.getElementById('btnEntrar').addEventListener('click', tentarLogin);

  document.getElementById('loginUser').addEventListener('keydown', e => {{
    if(e.key === 'Enter') tentarLogin();
  }});
  document.getElementById('loginPass').addEventListener('keydown', e => {{
    if(e.key === 'Enter') tentarLogin();
  }});
}})();

const splash    = document.getElementById('splash-screen');
const status    = document.getElementById('splashStatus');
const progress  = document.getElementById('splashProgress');
const progressB = document.getElementById('splashProgressBar');

function setStatus(msg, erro){{
  status.textContent = msg;
  status.className   = 'splash-status' + (erro ? ' erro' : '');
}}

function fecharSplashECarregar(total){{
  progressB.style.width = '100%';
  setStatus(`✓ Google Sheets — ${{total}} motorista(s) encontrado(s)`, false);
  setTimeout(()=>{{
    splash.style.transition = 'opacity .5s';
    splash.style.opacity    = '0';
    setTimeout(()=>{{ splash.style.display='none'; atualizarDashboardCompleto(); }}, 500);
  }}, 900);
}}

async function inicializar(){{
  progress.style.display = 'block';
  progressB.style.width  = '0%';
  setStatus('Conectando ao Google Sheets...', false);
  await new Promise(r => setTimeout(r, 400));
  progressB.style.width  = '40%';
  setStatus('Carregando motoristas...', false);
  await new Promise(r => setTimeout(r, 600));
  progressB.style.width  = '80%';
  await new Promise(r => setTimeout(r, 400));
  fecharSplashECarregar(motoristasDB.length);
}}
</script>
</body>
</html>
"""

HTML = HTML.replace("__ANO__", str(datetime.now().year))

# ─── Renderiza o HTML no Streamlit ────────────────────────────────────────────
components.html(HTML, height=800, scrolling=True)
