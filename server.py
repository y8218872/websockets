"""
نداء — خادم إشارات WebRTC (Signaling Server)
============================================
المتطلبات:  pip install flask flask-socketio
التشغيل:    python server.py
الفتح:      http://localhost:5000

ملاحظة: الفيديو/الصوت لا يمرّان عبر هذا الخادم أبدًا — يمرّان مباشرة بين
المتصفحين (P2P). الخادم يكتفي بالتعارف وتبادل عروض الاتصال SDP/ICE.
"""
import secrets
import time

from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__, static_folder=".", static_url_path="")
app.config["SECRET_KEY"] = secrets.token_hex(32)

# نبض سريع لاكتشاف الانقطاع مبكرًا على الشبكات الضعيفة
socketio = SocketIO(app, cors_allowed_origins="*",
                    ping_interval=5, ping_timeout=10)

rooms = {}                                   # room_code -> {sid: {"name":..}}
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # بلا حروف ملتبسة (0/O, 1/I…)


def new_code():
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(4))
        if code not in rooms:
            return code


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@socketio.on("join")
def on_join(data):
    sid = request.sid
    name = str(data.get("name") or "ضيف").strip()[:24] or "ضيف"
    room = str(data.get("room") or "").strip().upper() or new_code()

    join_room(room)
    members = rooms.setdefault(room, {})
    peers = [{"id": s, "name": m["name"]} for s, m in members.items()]
    members[sid] = {"name": name, "t": time.time()}

    emit("joined", {"room": room, "id": sid, "name": name, "peers": peers})
    emit("peer-joined", {"id": sid, "name": name}, room=room, include_self=False)
    emit("count", {"n": len(members)}, room=room)


@socketio.on("signal")
def on_signal(data):
    """ترحيل عروض/إجابات SDP ومرشّحات ICE بين طرفين فقط."""
    emit("signal", {"from": request.sid, "data": data["data"]}, room=data["to"])


@socketio.on("leave")
def on_leave(data):
    _remove(request.sid, data.get("room"))


@socketio.on("disconnect")
def on_disconnect():
    for room in list(rooms):
        if request.sid in rooms.get(room, {}):
            _remove(request.sid, room)


def _remove(sid, room):
    members = rooms.get(room)
    if not members or sid not in members:
        return
    del members[sid]
    leave_room(room)
    emit("peer-left", {"id": sid}, room=room)
    emit("count", {"n": len(members)}, room=room)
    if not members:
        del rooms[room]


if __name__ == "__main__":
    print("📡 نداء يعمل على  http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
