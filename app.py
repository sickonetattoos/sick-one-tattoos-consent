"""
Sick One Tattoos / Laser Tattoo Solutions — Consent Form App
Serves both the tattoo consent form and the laser removal consent form,
and emails completed submissions via SendGrid HTTP API.
Uses only Python stdlib (urllib) — no external HTTP library needed.
"""

import os, base64, json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max

RECIPIENT_EMAIL  = "laser.tattoo.solutions@gmail.com"
SENDER_EMAIL     = "laser.tattoo.solutions@gmail.com"
SENDER_NAME      = "Consent Forms"
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDGRID_URL     = "https://api.sendgrid.com/v3/mail/send"


# ─────────────────────────────────────────────────────────────
#  SHARED HELPERS
# ─────────────────────────────────────────────────────────────

def decode_b64(data_url):
    if data_url and "," in data_url:
        return base64.b64decode(data_url.split(",", 1)[1])
    return None


def send_via_sendgrid(payload):
    """Send a pre-built SendGrid payload dict. Returns (success, status_code)."""
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        SENDGRID_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urlopen(req, timeout=30) as resp:
        return resp.status


def build_attachments(jpeg_bytes, id_front_bytes, id_back_bytes, safe_name, date_str):
    attachments = []
    def add(file_bytes, filename):
        attachments.append({
            "content": base64.b64encode(file_bytes).decode(),
            "type": "image/jpeg",
            "filename": filename,
            "disposition": "attachment"
        })
    if jpeg_bytes:
        add(jpeg_bytes, f"ConsentForm_{safe_name}_{date_str}.jpg")
    if id_front_bytes:
        add(id_front_bytes, f"ID_Front_{safe_name}_{date_str}.jpg")
    if id_back_bytes:
        add(id_back_bytes, f"ID_Back_{safe_name}_{date_str}.jpg")
    return attachments


# ─────────────────────────────────────────────────────────────
#  ROUTES — TATTOO FORM
# ─────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Sick One Tattoos / Laser Tattoo Solutions Consent"})


@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data received"}), 400

        client_name  = data.get("clientName",  "Unknown Client")
        client_phone = data.get("clientPhone", "N/A")
        client_email = data.get("clientEmail", "N/A")
        artist_name  = data.get("artistName",  "N/A")
        procedure_dt = data.get("procedureDate","N/A")
        placement    = data.get("placement",   "N/A")
        design       = data.get("design",      "N/A")
        price        = data.get("price",       "N/A")
        submitted_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        safe_name    = client_name.replace(" ", "_")
        date_str     = datetime.now().strftime("%Y%m%d")

        jpeg_bytes     = decode_b64(data.get("jpegDataUrl", ""))
        id_front_bytes = decode_b64(data.get("idFrontDataUrl", ""))
        id_back_bytes  = decode_b64(data.get("idBackDataUrl", ""))

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;
                    background:#0d0d0d;color:#fff;border-radius:12px;overflow:hidden;">
          <div style="background:#c8a84b;padding:18px 28px;">
            <h1 style="margin:0;font-size:20px;color:#000;letter-spacing:1px;">
              SICK ONE TATTOOS</h1>
            <p style="margin:4px 0 0;font-size:12px;color:#333;">
              New Consent Form Submission</p>
          </div>
          <div style="padding:22px 28px;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;width:38%;">
                    Client Name</td>
                  <td style="padding:7px 0;">{client_name}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Phone</td>
                  <td style="padding:7px 0;">{client_phone}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Email</td>
                  <td style="padding:7px 0;">{client_email}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Artist</td>
                  <td style="padding:7px 0;">{artist_name}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">
                    Procedure Date</td>
                  <td style="padding:7px 0;">{procedure_dt}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Placement</td>
                  <td style="padding:7px 0;">{placement}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Design</td>
                  <td style="padding:7px 0;">{design}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Quoted Price</td>
                  <td style="padding:7px 0;">{price}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Submitted</td>
                  <td style="padding:7px 0;">{submitted_at}</td></tr>
            </table>
            <hr style="border:1px solid #333;margin:18px 0;">
            <p style="color:#aaa;font-size:13px;margin:0;">
              Completed consent form JPEG attached. ID photo(s) attached if provided.</p>
          </div>
          <div style="background:#111;padding:10px 28px;text-align:center;">
            <p style="margin:0;font-size:11px;color:#555;">
              Sick One Tattoos &middot; SNHD Compliant Consent System</p>
          </div>
        </div>"""

        attachments = build_attachments(jpeg_bytes, id_front_bytes, id_back_bytes, safe_name, date_str)
        sg_payload = {
            "personalizations": [{
                "to": [{"email": RECIPIENT_EMAIL}],
                "subject": f"[Tattoo Consent] {client_name} — {submitted_at}"
            }],
            "from": {"email": SENDER_EMAIL, "name": "Sick One Tattoos Forms"},
            "content": [{"type": "text/html", "value": html}],
        }
        if attachments:
            sg_payload["attachments"] = attachments

        status = send_via_sendgrid(sg_payload)

        if status in (200, 202):
            print(f"[OK] Tattoo consent email sent for: {client_name}")
            return jsonify({"success": True}), 200
        else:
            print(f"[ERROR] SendGrid returned status {status}")
            return jsonify({"error": f"SendGrid error {status}"}), 500

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] SendGrid HTTP {e.code}: {body}")
        return jsonify({"error": f"SendGrid error {e.code}: {body}"}), 500
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────
#  ROUTES — LASER FORM
# ─────────────────────────────────────────────────────────────

@app.route("/laser", methods=["GET"])
def laser():
    return render_template("laser.html")


@app.route("/laser-submit", methods=["POST"])
def laser_submit():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data received"}), 400

        client_name  = data.get("clientName",  "Unknown Client")
        client_phone = data.get("clientPhone", "N/A")
        client_email = data.get("clientEmail", "N/A")
        tech_name    = data.get("techName",    "N/A")
        procedure_dt = data.get("procedureDate","N/A")
        placement    = data.get("placement",   "N/A")
        session      = data.get("session",     "N/A")
        ink_colors   = data.get("inkColors",   "N/A")
        price        = data.get("price",       "N/A")
        submitted_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        safe_name    = client_name.replace(" ", "_")
        date_str     = datetime.now().strftime("%Y%m%d")

        jpeg_bytes     = decode_b64(data.get("jpegDataUrl", ""))
        id_front_bytes = decode_b64(data.get("idFrontDataUrl", ""))
        id_back_bytes  = decode_b64(data.get("idBackDataUrl", ""))

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;
                    background:#0d0d0d;color:#fff;border-radius:12px;overflow:hidden;">
          <div style="background:#c8a84b;padding:18px 28px;">
            <h1 style="margin:0;font-size:20px;color:#000;letter-spacing:1px;">
              LASER TATTOO SOLUTIONS</h1>
            <p style="margin:4px 0 0;font-size:12px;color:#333;">
              New Laser Removal Consent Form Submission</p>
          </div>
          <div style="padding:22px 28px;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;width:38%;">
                    Client Name</td>
                  <td style="padding:7px 0;">{client_name}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Phone</td>
                  <td style="padding:7px 0;">{client_phone}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Email</td>
                  <td style="padding:7px 0;">{client_email}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Technician</td>
                  <td style="padding:7px 0;">{tech_name}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">
                    Treatment Date</td>
                  <td style="padding:7px 0;">{procedure_dt}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Treatment Area</td>
                  <td style="padding:7px 0;">{placement}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Session #</td>
                  <td style="padding:7px 0;">{session}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Ink Colors</td>
                  <td style="padding:7px 0;">{ink_colors}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Quoted Price</td>
                  <td style="padding:7px 0;">{price}</td></tr>
              <tr><td style="padding:7px 0;color:#c8a84b;font-weight:bold;">Submitted</td>
                  <td style="padding:7px 0;">{submitted_at}</td></tr>
            </table>
            <hr style="border:1px solid #333;margin:18px 0;">
            <p style="color:#aaa;font-size:13px;margin:0;">
              Completed consent form JPEG attached. ID photo(s) attached if provided.</p>
          </div>
          <div style="background:#111;padding:10px 28px;text-align:center;">
            <p style="margin:0;font-size:11px;color:#555;">
              Laser Tattoo Solutions &middot; Laser Removal Consent System</p>
          </div>
        </div>"""

        attachments = build_attachments(jpeg_bytes, id_front_bytes, id_back_bytes, safe_name, date_str)
        sg_payload = {
            "personalizations": [{
                "to": [{"email": RECIPIENT_EMAIL}],
                "subject": f"[Laser Removal Consent] {client_name} — {submitted_at}"
            }],
            "from": {"email": SENDER_EMAIL, "name": "Laser Tattoo Solutions Forms"},
            "content": [{"type": "text/html", "value": html}],
        }
        if attachments:
            sg_payload["attachments"] = attachments

        status = send_via_sendgrid(sg_payload)

        if status in (200, 202):
            print(f"[OK] Laser consent email sent for: {client_name}")
            return jsonify({"success": True}), 200
        else:
            print(f"[ERROR] SendGrid returned status {status}")
            return jsonify({"error": f"SendGrid error {status}"}), 500

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] SendGrid HTTP {e.code}: {body}")
        return jsonify({"error": f"SendGrid error {e.code}: {body}"}), 500
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
