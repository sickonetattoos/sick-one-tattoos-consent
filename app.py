"""
Sick One Tattoos — Consent Form App
Serves the form and emails completed submissions to the shop Gmail.
"""

import os, smtplib, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

RECIPIENT_EMAIL = "laser.tattoo.solutions@gmail.com"
SENDER_EMAIL    = "laser.tattoo.solutions@gmail.com"
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "aelczljtawyrobbq")
SMTP_HOST       = "smtp.gmail.com"
SMTP_PORT       = 587

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Sick One Tattoos Consent"})

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

        def decode_b64(data_url):
            if data_url and "," in data_url:
                return base64.b64decode(data_url.split(",", 1)[1])
            return None

        jpeg_bytes     = decode_b64(data.get("jpegDataUrl", ""))
        id_front_bytes = decode_b64(data.get("idFrontDataUrl", ""))
        id_back_bytes  = decode_b64(data.get("idBackDataUrl", ""))

        # ── Build email ──────────────────────────────────────
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"✅ New Consent Form — {client_name} ({submitted_at})"
        msg["From"]    = f"Sick One Tattoos Forms <{SENDER_EMAIL}>"
        msg["To"]      = RECIPIENT_EMAIL

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
              Sick One Tattoos · SNHD Compliant Consent System</p>
          </div>
        </div>"""
        msg.attach(MIMEText(html, "html"))

        def attach_file(file_bytes, filename):
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f'attachment; filename="{filename}"')
            part.add_header("Content-Type", "image/jpeg")
            msg.attach(part)

        if jpeg_bytes:
            attach_file(jpeg_bytes,
                        f"ConsentForm_{safe_name}_{date_str}.jpg")
        if id_front_bytes:
            attach_file(id_front_bytes,
                        f"ID_Front_{safe_name}_{date_str}.jpg")
        if id_back_bytes:
            attach_file(id_back_bytes,
                        f"ID_Back_{safe_name}_{date_str}.jpg")

        # ── Send via Gmail SMTP ──────────────────────────────
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(SENDER_EMAIL, SENDER_PASSWORD)
            srv.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

        print(f"[OK] Email sent for: {client_name}")
        return jsonify({"success": True}), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
