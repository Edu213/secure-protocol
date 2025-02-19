from flask import Flask, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
import random
import string

app = Flask(__name__)
app.secret_key = 'CriptografiaProyecto'
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app)



rooms = {}

def generate_room_code(length: int, existing_codes: list[str]) -> str:
    while True:
        code_chars = [random.choice(string.ascii_letters) for _ in range (length)]
        code = ''.join(code_chars)

        if code not in existing_codes:
            return code

@app.route('/', methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get('name')
        create = request.form.get('create', False)
        code = request.form.get('code')
        join = request.form.get('join', False)
        if not name:
            return render_template('home.html', error="Name is required", code=code, rooms=rooms)
        if create != False:
            room_code = generate_room_code(6, list(rooms.keys()))
            new_room = {
                'members': 0,
                'messages': [],
                'creator': name
            }
            rooms[room_code] = new_room
            print("Salas activas:", rooms)
        if join != False:
            # no code
            if not code:
                return render_template('home.html', error="Please enter a room code to enter a chat room", name=name)
            # invalid code
            if code not in rooms:
                return render_template('home.html', error="Room code invalid", name=name)
            room_code = code
        session['room'] = room_code
        session['name'] = name
        return redirect(url_for('room'))
    else:
        return render_template('home.html', rooms=rooms)

@app.route('/room')
def room():
    room = session.get('room')
    name = session.get('name')

    if name is None or room is None or room not in rooms:
        return redirect(url_for('home'))
    messages =  rooms[room]['messages']    

    return render_template('room.html', room=room, user=name, messages=messages)

@socketio.on('connect')
def handle_connect():
    name = session.get('name')
    room = session.get('room')

    if name is None or room is None:
        return
    if room not in rooms:
        leave_room(room)
    join_room(room)
    send({
        "sender": "",
        "message": f"{name} entro al chat"
    }, to=room)
    rooms[room]["members"] += 1

@socketio.on('message')
def handle_message(payload):
    room = session.get('room')
    name = session.get('name')

    if room not in rooms:
        return
    message = {
        "sender": name,
        "message": payload["message"]
    }
    send(message, to=room)
    rooms[room]["messages"].append(message)

@socketio.on('disconnect')
def handle_disconnect():
    room = session.get('room')
    name = session.get("name")
    leave_room
    
    if room in rooms:
        rooms[room]["members"] -= 1

        if rooms[room]["members"] <= 0:
            del rooms[room]
        send({
            "message": f"{name} ha dejado el chat",
            "sender": ""
        })
if __name__ == "__main__":
    socketio.run(app, debug=True)
