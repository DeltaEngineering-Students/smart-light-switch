#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <Update.h>
#include <WiFiClientSecure.h>
#include <HTTPUpdate.h>
#include "icon_data.h"
#include "secrets.h"  // WIFI_SSID, WIFI_PASS, AP_SSID, AP_PASS, OTA_PASS (не комітиться, див. secrets.example.h)



constexpr int SERVO_PIN    = 13;
constexpr int BUTTON_PIN   = 14;
constexpr int LED_PIN      = 2;

constexpr int SERVO_CHANEL = 0;
constexpr int SERVO_FREQ   = 50;
constexpr int SERVO_RES    = 16;

const char FIRMWARE_VERSION[] = "v1.3.0 (Auto-Detach 30s)";

// Максимально можливий апаратний діапазон ШІМ-імпульсів під шкалу 0°..360° (300..2700 мкс)
int minPulseUs   = 300;   // 0°   (крайній мінімум декодера серви)
int maxPulseUs   = 2700;  // 360° (крайній максимум декодера серви)

Preferences prefs;
WebServer server(80);

int angleNeutral = 180;   // Середина шкали 0..360° (1500 мкс)
int angleOn      = 240;
int angleOff     = 120;
int pushTimeMs   = 260;
int stepDelayMs  = 0;
int currentAngle = 180;
bool lightState  = false;

unsigned long releaseAtMs = 0;
bool lastBtnState = HIGH;
unsigned long lastBtnTime = 0;

int angleToUs(int angle) {
    angle = constrain(angle, 0, 360);
    return map(angle, 0, 360, minPulseUs, maxPulseUs);
}

bool isServoAttached = false;

void servoAttachPwm() {
    if (isServoAttached) return;
#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
    ledcAttach(SERVO_PIN, SERVO_FREQ, SERVO_RES);
#else
    ledcAttachPin(SERVO_PIN, SERVO_CHANEL);
#endif
    isServoAttached = true;
}

void servoStopPwm() {
    if (!isServoAttached) return;
#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
    ledcDetach(SERVO_PIN);
#else
    ledcDetachPin(SERVO_PIN);
#endif
    pinMode(SERVO_PIN, INPUT_PULLDOWN);
    isServoAttached = false;
}

void writePulseUs(int pulseUs) {
    servoAttachPwm();
    pulseUs = constrain(pulseUs, 200, 2800);
    uint32_t duty = (uint32_t)((pulseUs * 65536UL) / 20000UL);
#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
    ledcWrite(SERVO_PIN, duty);
#else
    ledcWrite(SERVO_CHANEL, duty);
#endif
}

void servoMoveTo(int targetAngle, int delayPerDeg) {
    targetAngle = constrain(targetAngle, 0, 360);
    if (delayPerDeg <= 0 || abs(targetAngle - currentAngle) <= 2) {
        currentAngle = targetAngle;
        writePulseUs(angleToUs(currentAngle));
        return;
    }
    int step = (targetAngle > currentAngle) ? 1 : -1;
    while (currentAngle != targetAngle) {
        currentAngle += step;
        writePulseUs(angleToUs(currentAngle));
        delay(delayPerDeg);
    }
}

void triggerSwitch(bool turnOn) {
    digitalWrite(LED_PIN, HIGH);
    int targetAngle = turnOn ? angleOn : angleOff;

    servoMoveTo(targetAngle, stepDelayMs);
    delay(pushTimeMs);

    servoMoveTo(angleNeutral, stepDelayMs);
    delay(260);

    releaseAtMs = millis() + 30000UL; // 30 секунд активного утримання нейтралі, потім вільний стан
    lightState = turnOn;
    digitalWrite(LED_PIN, LOW);
}

const char HTML_PAGE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#090b10">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Світло">
<link rel="apple-touch-icon" href="/icon.png">
<link rel="icon" type="image/png" href="/icon.png">
<link rel="manifest" href="/manifest.json">
<title>Smart Switch 360°</title>
<style>
  :root {
    --bg: #090b10;
    --surface: rgba(22, 27, 38, 0.9);
    --border: rgba(255, 255, 255, 0.08);
    --accent: #3b82f6;
    --on-grad: linear-gradient(145deg, #10b981, #047857);
    --off-grad: linear-gradient(145deg, #ef4444, #b91c1c);
    --text: #f9fafb;
    --muted: #9ca3af;
  }
  * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif; -webkit-tap-highlight-color: transparent; }
  html { background-color: #090b10; height: 100%; }
  body {
    margin: 0;
    padding: env(safe-area-inset-top, 20px) 16px env(safe-area-inset-bottom, 20px) 16px;
    min-height: 100dvh;
    background-color: #090b10;
    background-image: radial-gradient(circle at 50% 0%, #162038 0%, #090b10 70%);
    color: var(--text);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    overscroll-behavior: none;
  }
  .app { width: 100%; max-width: 390px; }
  .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
  .brand { display: flex; align-items: center; gap: 10px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; background: #10b981; box-shadow: 0 0 12px #10b981; }
  .title { font-size: 17px; font-weight: 800; letter-spacing: 0.8px; }
  .gear-btn {
    background: var(--surface); border: 1px solid var(--border); color: var(--text);
    width: 44px; height: 44px; border-radius: 14px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.15s, background 0.15s;
  }
  .gear-btn:active { transform: scale(0.92); background: rgba(59,130,246,0.2); }
  .icon-svg { width: 22px; height: 22px; stroke: currentColor; stroke-width: 2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .btn-svg { width: 34px; height: 34px; stroke: #ffffff; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; margin-bottom: 4px; }

  .main-grid { display: grid; grid-template-columns: 1fr; gap: 16px; margin-bottom: 20px; }
  .power-btn {
    border: 1px solid rgba(255,255,255,0.12); border-radius: 24px; padding: 38px 20px;
    color: #fff; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 6px;
    transition: transform 0.12s, box-shadow 0.12s;
  }
  .power-btn:active { transform: scale(0.96); }
  .btn-on { background: var(--on-grad); box-shadow: 0 14px 32px -6px rgba(16, 185, 129, 0.42); }
  .btn-off { background: var(--off-grad); box-shadow: 0 14px 32px -6px rgba(239, 68, 68, 0.38); }
  .power-label { font-size: 23px; font-weight: 800; letter-spacing: 1px; }
  .power-sub { font-size: 13px; opacity: 0.82; font-weight: 500; }

  .status-pill {
    text-align: center; font-size: 13px; color: var(--muted);
    background: var(--surface); border: 1px solid var(--border);
    padding: 13px 16px; border-radius: 14px; font-weight: 500;
  }

  .modal-backdrop {
    position: fixed; inset: 0; background: rgba(0, 0, 0, 0.78); backdrop-filter: blur(8px);
    display: none; align-items: flex-end; justify-content: center; z-index: 50; padding: 12px;
  }
  .modal-backdrop.open { display: flex; }
  .modal {
    width: 100%; max-width: 410px; max-height: 90dvh; overflow-y: auto;
    background: #121620; border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px; padding: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.7);
  }
  .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .modal-title { font-size: 16px; font-weight: 800; letter-spacing: 0.3px; }
  .close-btn {
    background: #1e2433; border: 1px solid var(--border); color: #fff;
    width: 34px; height: 34px; border-radius: 10px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
  }

  .section { background: #0c0f16; border: 1px solid var(--border); border-radius: 16px; padding: 14px; margin-bottom: 14px; }
  .section-title { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.7px; }
  .live-deg { font-size: 28px; font-weight: 800; color: #60a5fa; text-align: center; }
  .live-us { font-size: 12px; color: var(--muted); display: block; text-align: center; margin-bottom: 6px; }
  input[type=range] { width: 100%; height: 8px; border-radius: 4px; accent-color: var(--accent); margin: 10px 0; cursor: pointer; }
  .cap-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 8px; }
  .step-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 6px; margin-top: 8px; }
  .cap-btn { padding: 10px 4px; border-radius: 10px; border: 1px solid #283040; background: #161b26; color: #fff; font-size: 11px; font-weight: 700; cursor: pointer; }
  .cap-btn:active { background: var(--accent); }

  .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .row:last-child { margin-bottom: 0; }
  .row label { font-size: 13px; color: #e5e7eb; }
  .row input[type=number] { width: 82px; padding: 8px; border-radius: 10px; border: 1px solid #283040; background: #161b26; color: #fff; font-size: 14px; font-weight: 700; text-align: center; }

  .save-btn { width: 100%; padding: 14px; border: none; border-radius: 14px; background: var(--accent); color: #fff; font-weight: 800; font-size: 15px; cursor: pointer; margin-top: 4px; }
</style>
</head>
<body>
<div class="app">
  <div class="top-bar">
    <div class="brand">
      <div class="dot"></div>
      <div>
        <div class="title">SMART SWITCH 360°</div>
        <div style="font-size:10px;color:var(--muted);font-weight:600">%FW_VER%</div>
      </div>
    </div>
    <button class="gear-btn" onclick="toggleSettings(true)" aria-label="Settings">
      <svg class="icon-svg" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
      </svg>
    </button>
  </div>

  <div class="main-grid">
    <button class="power-btn btn-on" onclick="act('on')">
      <svg class="btn-svg" viewBox="0 0 24 24">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
      </svg>
      <span class="power-label">УВІМКНУТИ</span>
      <span class="power-sub">Світло ON</span>
    </button>
    <button class="power-btn btn-off" onclick="act('off')">
      <svg class="btn-svg" viewBox="0 0 24 24">
        <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
        <line x1="12" y1="2" x2="12" y2="12"></line>
      </svg>
      <span class="power-label">ВИМКНУТИ</span>
      <span class="power-sub">Світло OFF</span>
    </button>
  </div>

  <div class="status-pill" id="st">Шкала 0°..360° (300..2700 мкс) активна</div>
</div>

<div class="modal-backdrop" id="modalBg" onclick="if(event.target===this)toggleSettings(false)">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title">Калібрування (0°..360°)</div>
      <button class="close-btn" onclick="toggleSettings(false)" aria-label="Close">
        <svg class="icon-svg" style="width:18px;height:18px" viewBox="0 0 24 24">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="section">
      <div class="section-title">Повний пошук кута (0°..360°)</div>
      <div class="live-deg" id="liveDeg">%CUR%°</div>
      <span class="live-us" id="liveUs">1500 мкс</span>
      <input type="range" id="slider" min="0" max="360" value="%CUR%" oninput="onSlide(this.value)">
      <div class="step-grid">
        <button class="cap-btn" onclick="stepDeg(-10)">-10°</button>
        <button class="cap-btn" onclick="stepDeg(-2)">-2°</button>
        <button class="cap-btn" onclick="stepDeg(2)">+2°</button>
        <button class="cap-btn" onclick="stepDeg(10)">+10°</button>
      </div>
      <div class="cap-grid">
        <button class="cap-btn" onclick="capture('off')">Записати<br>як OFF</button>
        <button class="cap-btn" onclick="capture('neutral')">Записати<br>як Центр</button>
        <button class="cap-btn" onclick="capture('on')">Записати<br>як ON</button>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Кути (0°..360°)</div>
      <div class="row">
        <label>Нейтраль (Центр):</label>
        <input type="number" id="neutral" min="0" max="360" value="%NEUTRAL%">
      </div>
      <div class="row">
        <label>Кут УВІМК (ON):</label>
        <input type="number" id="on" min="0" max="360" value="%ON%">
      </div>
      <div class="row">
        <label>Кут ВИМК (OFF):</label>
        <input type="number" id="off" min="0" max="360" value="%OFF%">
      </div>
    </div>

    <div class="section">
      <div class="section-title">Швидкість та Межі ШІМ</div>
      <div class="row">
        <label>Затримка кроку (0 = макс.):</label>
        <input type="number" id="spd" min="0" max="15" value="%SPD%">
      </div>
      <div class="row">
        <label>Час дотиску клавіші (мс):</label>
        <input type="number" id="hold" min="100" max="1000" step="20" value="%HOLD%">
      </div>
      <div class="row">
        <label>Мін. імпульс 0° (мкс):</label>
        <input type="number" id="minUs" min="200" max="1200" step="50" value="%MIN_US%">
      </div>
      <div class="row">
        <label>Макс. імпульс 360° (мкс):</label>
        <input type="number" id="maxUs" min="1800" max="2800" step="50" value="%MAX_US%">
      </div>
    </div>

    <div class="section">
      <div class="section-title">Система та Оновлення</div>
      <div class="row"><label>Версія ПЗ:</label><span id="sysVer" style="color:#10b981;font-weight:700">%FW_VER%</span></div>
      <div class="row"><label>Стан мотора:</label><span id="sysServo" style="color:#38bdf8;font-weight:700">...</span></div>
      <div class="row"><label>Wi-Fi:</label><span id="sysWifi">...</span></div>
      <div class="row"><label>IP:</label><span id="sysIp">...</span></div>
      <div class="row"><label>Сигнал:</label><span id="sysRssi">...</span></div>
      <div class="row"><label>Аптайм:</label><span id="sysUp">...</span></div>
      <button class="cal-btn" onclick="rebootEsp()" style="margin-bottom:8px">Перезавантажити ESP32</button>
      <button class="cal-btn" style="background:#059669;border-color:#10b981;color:#fff;font-weight:700" onclick="otaGithub()">⚡ Оновити прошивку з GitHub (CI/CD)</button>
      <div id="otaStatus" style="font-size:11px;color:var(--muted);text-align:center;margin-top:6px"></div>
    </div>

    <button class="save-btn" onclick="saveCfg()">Зберегти налаштування</button>
  </div>
</div>

<script>
let busy = false;
let pendingVal = null;

function toggleSettings(open) {
  document.getElementById('modalBg').classList.toggle('open', open);
  if (open) loadSys();
}

async function loadSys() {
  try {
    const j = await (await fetch('/api/sys')).json();
    if (j.ver) document.getElementById('sysVer').innerText = j.ver;
    if (j.servo) document.getElementById('sysServo').innerText = j.servo;
    document.getElementById('sysWifi').innerText = j.sta ? 'підключено' : 'НЕ підключено (лише AP)';
    document.getElementById('sysIp').innerText = j.sta ? j.ip : '192.168.4.1';
    document.getElementById('sysRssi').innerText = j.sta ? j.rssi + ' dBm' : '-';
    const m = Math.floor(j.up / 60);
    document.getElementById('sysUp').innerText = Math.floor(m / 60) + ' год ' + (m % 60) + ' хв';
  } catch(e) {}
}

async function rebootEsp() {
  if (!confirm('Перезавантажити ESP32? Сторінка буде недоступна ~15 секунд.')) return;
  document.getElementById('st').innerText = 'Перезавантаження...';
  toggleSettings(false);
  try { await fetch('/api/reboot'); } catch(e) {}
  setTimeout(() => location.reload(), 15000);
}

async function otaGithub() {
  if (!confirm('Завантажити останній реліз із GitHub CI/CD та перепрошити ESP32 по Wi-Fi?')) return;
  const st = document.getElementById('otaStatus');
  st.innerText = 'Завантаження з GitHub... Зачекай ~45 сек.';
  try {
    const res = await fetch('/api/ota/github');
    const txt = await res.text();
    st.innerText = txt;
  } catch(e) {
    st.innerText = 'Запит надіслано! ESP32 оновлюється...';
  }
  setTimeout(() => location.reload(), 45000);
}

function degToUs(d) {
  const minU = parseInt(document.getElementById('minUs').value || 300);
  const maxU = parseInt(document.getElementById('maxUs').value || 2700);
  return Math.round(minU + (d / 360.0) * (maxU - minU));
}

function stepDeg(delta) {
  const s = document.getElementById('slider');
  let v = Math.min(360, Math.max(0, parseInt(s.value) + delta));
  s.value = v;
  onSlide(v);
}

async function onSlide(val) {
  document.getElementById('liveDeg').innerText = val + '°';
  document.getElementById('liveUs').innerText = degToUs(val) + ' мкс';
  pendingVal = val;
  if (busy) return;
  busy = true;
  while (pendingVal !== null) {
    let v = pendingVal;
    pendingVal = null;
    try { await fetch('/api/move?deg=' + v); } catch(e) {}
  }
  busy = false;
}

function capture(which) {
  const cur = document.getElementById('slider').value;
  document.getElementById(which).value = cur;
  saveCfg();
}

async function act(cmd) {
  document.getElementById('st').innerText = 'Виконую...';
  const r = await fetch('/api/act?cmd=' + cmd);
  document.getElementById('st').innerText = await r.text();
}

async function saveCfg() {
  const n = document.getElementById('neutral').value;
  const on = document.getElementById('on').value;
  const off = document.getElementById('off').value;
  const h = document.getElementById('hold').value;
  const s = document.getElementById('spd').value;
  const minU = document.getElementById('minUs').value;
  const maxU = document.getElementById('maxUs').value;
  const r = await fetch(`/api/cfg?n=${n}&on=${on}&off=${off}&h=${h}&s=${s}&minu=${minU}&maxu=${maxU}`);
  document.getElementById('st').innerText = await r.text();
  toggleSettings(false);
}
</script>
</body>
</html>
)rawliteral";

void handleRoot() {
    String page = FPSTR(HTML_PAGE);
    page.replace("%CUR%", String(currentAngle));
    page.replace("%NEUTRAL%", String(angleNeutral));
    page.replace("%ON%", String(angleOn));
    page.replace("%OFF%", String(angleOff));
    page.replace("%HOLD%", String(pushTimeMs));
    page.replace("%SPD%", String(stepDelayMs));
    page.replace("%MIN_US%", String(minPulseUs));
    page.replace("%MAX_US%", String(maxPulseUs));
    page.replace("%FW_VER%", FIRMWARE_VERSION);
    server.send(200, "text/html", page);
}

void handleMove() {
    if (!server.hasArg("deg")) {
        server.send(400, "text/plain", "Missing deg");
        return;
    }
    int deg = constrain(server.arg("deg").toInt(), 0, 360);
    servoMoveTo(deg, 0);
    releaseAtMs = millis() + 30000UL;
    server.send(200, "text/plain", "OK");
}

void handleAct() {
    String cmd = server.arg("cmd");
    if (cmd == "on") {
        triggerSwitch(true);
        server.send(200, "text/plain", "Світло УВІМКНЕНО • Розтиск через 30с");
    } else if (cmd == "off") {
        triggerSwitch(false);
        server.send(200, "text/plain", "Світло ВИМКНЕНО • Розтиск через 30с");
    } else {
        server.send(400, "text/plain", "Unknown cmd");
    }
}

void handleSys() {
    bool sta = WiFi.status() == WL_CONNECTED;
    String j = "{\"sta\":" + String(sta ? "true" : "false") +
               ",\"ip\":\"" + WiFi.localIP().toString() +
               "\",\"rssi\":" + String(sta ? WiFi.RSSI() : 0) +
               ",\"up\":" + String(millis() / 1000) +
               ",\"ver\":\"" + String(FIRMWARE_VERSION) + "\"" +
               ",\"servo\":\"" + String(isServoAttached ? "Активна (тримає)" : "Вільна (0 мА)") + "\"}";
    server.send(200, "application/json", j);
}

void handleIcon() {
    server.sendHeader("Cache-Control", "public, max-age=86400");
    server.send_P(200, "image/png", (const char*)ICON_PNG, ICON_PNG_LEN);
}

void handleManifest() {
    server.send(200, "application/manifest+json",
        "{\"name\":\"Smart Switch\",\"short_name\":\"Світло\",\"start_url\":\"/\","
        "\"display\":\"standalone\",\"background_color\":\"#090b10\",\"theme_color\":\"#090b10\","
        "\"icons\":[{\"src\":\"/icon.png\",\"sizes\":\"180x180\",\"type\":\"image/png\"}]}");
}

void handleReboot() {
    server.send(200, "text/plain", "Перезавантаження...");
    delay(300);
    ESP.restart();
}

void handleOtaGithub() {
    server.send(200, "text/plain", "Початок хмарного оновлення з GitHub...");
    delay(200);
    servoStopPwm();
    digitalWrite(LED_PIN, HIGH);

    WiFiClientSecure client;
    client.setInsecure();
    httpUpdate.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
    httpUpdate.rebootOnUpdate(true);

    Serial.println("[Cloud OTA] Завантаження прошивки з GitHub Releases...");
    t_httpUpdate_return ret = httpUpdate.update(client,
        "https://github.com/DeltaEngineering-Students/smart-light-switch/releases/latest/download/firmware.bin");

    if (ret == HTTP_UPDATE_FAILED) {
        Serial.printf("[Cloud OTA] Помилка (%d): %s\n", httpUpdate.getLastError(), httpUpdate.getLastErrorString().c_str());
    }
    digitalWrite(LED_PIN, LOW);
}

// Вотчдог Wi-Fi: автоперепідключення, а якщо довго немає зв'язку з роутером — повний рестарт
unsigned long lastWifiCheck = 0;
unsigned long wifiDownSince = 0;

void wifiWatchdog() {
    if (millis() - lastWifiCheck < 10000) return;
    lastWifiCheck = millis();

    if (WiFi.status() == WL_CONNECTED) {
        wifiDownSince = 0;
        return;
    }
    if (wifiDownSince == 0) wifiDownSince = millis();

    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    if (millis() - wifiDownSince > 180000UL) {
        ESP.restart();
    }
}

void handleCfg() {
    if (server.hasArg("n"))    angleNeutral = constrain(server.arg("n").toInt(), 0, 360);
    if (server.hasArg("on"))   angleOn      = constrain(server.arg("on").toInt(), 0, 360);
    if (server.hasArg("off"))  angleOff     = constrain(server.arg("off").toInt(), 0, 360);
    if (server.hasArg("h"))    pushTimeMs   = constrain(server.arg("h").toInt(), 100, 1000);
    if (server.hasArg("s"))    stepDelayMs  = constrain(server.arg("s").toInt(), 0, 15);
    if (server.hasArg("minu")) minPulseUs   = constrain(server.arg("minu").toInt(), 200, 1200);
    if (server.hasArg("maxu")) maxPulseUs   = constrain(server.arg("maxu").toInt(), 1800, 2800);

    prefs.putInt("neutral", angleNeutral);
    prefs.putInt("on", angleOn);
    prefs.putInt("off", angleOff);
    prefs.putInt("hold", pushTimeMs);
    prefs.putInt("spd", stepDelayMs);
    prefs.putInt("minu", minPulseUs);
    prefs.putInt("maxu", maxPulseUs);

    servoMoveTo(angleNeutral, stepDelayMs);
    releaseAtMs = millis() + 30000UL;
    server.send(200, "text/plain", "Збережено • Центр " + String(angleNeutral) + "°");
}

void setup() {
    setCpuFrequencyMhz(80);
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    prefs.begin("switch-360", false);
    angleNeutral = prefs.getInt("neutral", 180);
    angleOn      = prefs.getInt("on", 240);
    angleOff     = prefs.getInt("off", 120);
    pushTimeMs   = prefs.getInt("hold", 260);
    stepDelayMs  = prefs.getInt("spd", 0);
    minPulseUs   = prefs.getInt("minu", 300);
    maxPulseUs   = prefs.getInt("maxu", 2700);
    currentAngle = angleNeutral;

#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
    ledcAttach(SERVO_PIN, SERVO_FREQ, SERVO_RES);
#else
    ledcSetup(SERVO_CHANEL, SERVO_FREQ, SERVO_RES);
    ledcAttachPin(SERVO_PIN, SERVO_CHANEL);
#endif
    isServoAttached = true;

    writePulseUs(angleToUs(angleNeutral));
    releaseAtMs = millis() + 30000UL;

    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_SSID, AP_PASS);
    WiFi.setSleep(true);
    WiFi.setAutoReconnect(true);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    unsigned long startAttempt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 10000) {
        delay(250);
    }

    Serial.println();
    Serial.print("Connected IP: ");
    Serial.println(WiFi.localIP());

    MDNS.begin("switch");

    server.on("/", handleRoot);
    server.on("/api/move", handleMove);
    server.on("/api/act", handleAct);
    server.on("/api/cfg", handleCfg);
    server.on("/api/sys", handleSys);
    server.on("/api/reboot", handleReboot);
    server.on("/api/ota/github", handleOtaGithub);
    server.on("/icon.png", handleIcon);
    server.on("/manifest.json", handleManifest);
    // Бездротова Web OTA прошивка через HTTP POST або через браузер (без залежності від порту espota)
    server.on("/update", HTTP_GET, []() {
        server.send(200, "text/html",
            "<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>OTA Update</title><style>body{font-family:sans-serif;background:#090b10;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}"
            ".card{background:#161b26;padding:24px;border-radius:16px;border:1px solid #283040;max-width:360px;width:100%;text-align:center}"
            "input[type=file]{margin:16px 0;color:#9ca3af}input[type=submit]{background:#3b82f6;color:#fff;border:none;padding:12px 24px;border-radius:10px;font-weight:700;cursor:pointer;width:100%}"
            "</style></head><body><div class='card'><h2>⚡ Бездротове OTA</h2>"
            "<form method='POST' action='/update' enctype='multipart/form-data'>"
            "<input type='file' name='firmware' accept='.bin' required><br>"
            "<input type='submit' value='Оновити прошивку по Wi-Fi'>"
            "</form></div></body></html>");
    });

    server.on("/update", HTTP_POST, []() {
        server.sendHeader("Connection", "close");
        if (Update.hasError()) {
            server.send(500, "text/plain", "FAIL: " + String(Update.errorString()));
        } else {
            server.send(200, "text/plain", "OK: Перезавантаження...");
            delay(300);
            ESP.restart();
        }
    }, []() {
        HTTPUpload& upload = server.upload();
        if (upload.status == UPLOAD_FILE_START) {
            servoStopPwm();
            digitalWrite(LED_PIN, HIGH);
            Serial.printf("HTTP OTA Start: %s\n", upload.filename.c_str());
            uint32_t maxSketchSpace = (ESP.getFreeSketchSpace() - 0x1000) & 0xFFFFF000;
            if (!Update.begin(maxSketchSpace, U_FLASH)) {
                Update.printError(Serial);
            }
        } else if (upload.status == UPLOAD_FILE_WRITE) {
            if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
                Update.printError(Serial);
            }
            yield();
        } else if (upload.status == UPLOAD_FILE_END) {
            if (Update.end(true)) {
                Serial.printf("HTTP OTA Success: %u bytes\n", upload.totalSize);
            } else {
                Update.printError(Serial);
            }
            digitalWrite(LED_PIN, LOW);
        } else if (upload.status == UPLOAD_FILE_ABORTED) {
            Update.end();
            digitalWrite(LED_PIN, LOW);
            Serial.println("HTTP OTA Aborted");
        }
    });
    server.begin();
}

void loop() {
    server.handleClient();
    wifiWatchdog();

    if (releaseAtMs > 0 && millis() > releaseAtMs) {
        servoStopPwm();
        releaseAtMs = 0;
    }

    bool btn = digitalRead(BUTTON_PIN);
    if (btn == LOW && lastBtnState == HIGH && (millis() - lastBtnTime > 300)) {
        lastBtnTime = millis();
        triggerSwitch(!lightState);
    }
    lastBtnState = btn;
}
