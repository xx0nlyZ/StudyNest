import json
from datetime import date as _date

from pyscript import window

PESO = "\u20b1"
OPEN_HOUR = 8
CLOSE_HOUR = 22
HOURS_PER_DAY = 24

KEY_USERS = "sn.users"
KEY_SESSION = "sn.session"
KEY_BOOKINGS = "sn.bookings"
KEY_COUNTERS = "sn.counters"
KEY_SEEDED = "sn.seeded"
KEY_GUEST = "sn.guest_email"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

TIME_SLOTS = [
    "08:00", "09:00", "10:00", "11:00", "12:00", "13:00",
    "14:00", "15:00", "16:00", "17:00", "18:00", "19:00",
]

SEATS = [
    {"id": "S01", "kind": "individual", "zone": "Window row", "row": 1, "col": 1, "rate": 25, "capacity": 1,
     "label": "Window Seat 01", "amenities": ["Window view", "Reading lamp", "Power outlet", "Ergonomic chair"]},
    {"id": "S02", "kind": "individual", "zone": "Window row", "row": 1, "col": 2, "rate": 25, "capacity": 1,
     "label": "Window Seat 02", "amenities": ["Window view", "Reading lamp", "Power outlet", "Ergonomic chair"]},
    {"id": "S03", "kind": "individual", "zone": "Window row", "row": 1, "col": 3, "rate": 25, "capacity": 1,
     "label": "Window Seat 03", "amenities": ["Window view", "Reading lamp", "Power outlet", "Ergonomic chair"]},
    {"id": "S04", "kind": "individual", "zone": "Quiet center", "row": 2, "col": 1, "rate": 20, "capacity": 1,
     "label": "Quiet Seat 04", "amenities": ["Power outlet", "Reading lamp", "Privacy divider", "Ergonomic chair"]},
    {"id": "S05", "kind": "individual", "zone": "Quiet center", "row": 2, "col": 2, "rate": 20, "capacity": 1,
     "label": "Quiet Seat 05", "amenities": ["Power outlet", "Reading lamp", "Privacy divider", "Ergonomic chair"]},
    {"id": "S06", "kind": "individual", "zone": "Quiet center", "row": 2, "col": 3, "rate": 20, "capacity": 1,
     "label": "Quiet Seat 06", "amenities": ["Power outlet", "Reading lamp", "Privacy divider", "Ergonomic chair"]},
    {"id": "S07", "kind": "individual", "zone": "Standard aisle", "row": 3, "col": 1, "rate": 15, "capacity": 1,
     "label": "Standard Seat 07", "amenities": ["Power outlet", "Wi-Fi", "Ergonomic chair"]},
    {"id": "S08", "kind": "individual", "zone": "Standard aisle", "row": 3, "col": 2, "rate": 15, "capacity": 1,
     "label": "Standard Seat 08", "amenities": ["Power outlet", "Wi-Fi", "Ergonomic chair"]},
    {"id": "S09", "kind": "individual", "zone": "Standard aisle", "row": 3, "col": 3, "rate": 15, "capacity": 1,
     "label": "Standard Seat 09", "amenities": ["Power outlet", "Wi-Fi", "Ergonomic chair"]},
    {"id": "S10", "kind": "individual", "zone": "Standard aisle", "row": 4, "col": 1, "rate": 15, "capacity": 1,
     "label": "Standard Seat 10", "amenities": ["Power outlet", "Wi-Fi", "Ergonomic chair"]},
    {"id": "S11", "kind": "individual", "zone": "Standard aisle", "row": 4, "col": 2, "rate": 15, "capacity": 1,
     "label": "Standard Seat 11", "amenities": ["Power outlet", "Wi-Fi", "Ergonomic chair"]},
    {"id": "S12", "kind": "individual", "zone": "Standard aisle", "row": 4, "col": 3, "rate": 15, "capacity": 1,
     "label": "Standard Seat 12", "amenities": ["Power outlet", "Wi-Fi", "Ergonomic chair"]},
    {"id": "G01", "kind": "group", "zone": "Group study area", "row": 5, "col": 1, "rate": 25, "capacity": 4,
     "label": "Group Table 01", "amenities": ["Whiteboard", "Power outlet", "Wi-Fi", "4 seats"]},
    {"id": "G02", "kind": "group", "zone": "Group study area", "row": 5, "col": 2, "rate": 25, "capacity": 6,
     "label": "Group Table 02", "amenities": ["Whiteboard", "Power outlet", "Wi-Fi", "6 seats"]},
    {"id": "G03", "kind": "group", "zone": "Group study area", "row": 5, "col": 3, "rate": 25, "capacity": 8,
     "label": "Group Table 03", "amenities": ["Whiteboard", "TV screen", "Power outlet", "8 seats"]},
]

SEAT_MAP = {s["id"]: s for s in SEATS}


def store_get(key, default=None):
    raw = window.localStorage.getItem(key)
    if raw is None or type(raw).__name__ == "JsNull":
        return default
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def store_set(key, value):
    window.localStorage.setItem(key, json.dumps(value))


def store_del(key):
    window.localStorage.removeItem(key)


def money(amount):
    return f"{PESO}{amount:,.0f}"


def money2(amount):
    return f"{PESO}{amount:,.2f}"


def today_iso():
    try:
        d = window.Date.new()
        return f"{d.getFullYear():04d}-{d.getMonth() + 1:02d}-{d.getDate():02d}"
    except Exception:
        return _date.today().isoformat()


def parse_iso(value):
    parts = str(value).split("-")
    return _date(int(parts[0]), int(parts[1]), int(parts[2]))


def fmt_date(value):
    d = parse_iso(value)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def fmt_date_short(value):
    d = parse_iso(value)
    return f"{MONTHS[d.month - 1][:3]} {d.day}"


def slot_label(slot):
    hour = int(slot.split(":")[0])
    suffix = "AM" if hour < 12 else "PM"
    base = hour % 12
    if base == 0:
        base = 12
    return f"{base}:00 {suffix}"


def slot_end_label(slot, duration):
    hour = int(slot.split(":")[0]) + int(duration)
    suffix = "AM" if hour < 12 else "PM"
    base = hour % 12
    if base == 0:
        base = 12
    return f"{base}:00 {suffix}"


def time_range(slot, duration):
    return f"{slot_label(slot)} \u2013 {slot_end_label(slot, duration)}"


def slot_index(slot):
    try:
        return TIME_SLOTS.index(slot)
    except ValueError:
        return -1


def slot_hour(slot):
    return int(slot.split(":")[0])


def max_duration_for(slot):
    return max(0, min(5, CLOSE_HOUR - slot_hour(slot)))


def overlaps(start_a, dur_a, start_b, dur_b):
    a1 = slot_hour(start_a)
    a2 = a1 + int(dur_a)
    b1 = slot_hour(start_b)
    b2 = b1 + int(dur_b)
    return a1 < b2 and b1 < a2


def load_users():
    return store_get(KEY_USERS, [])


def save_users(users):
    store_set(KEY_USERS, users)


def load_bookings():
    return store_get(KEY_BOOKINGS, [])


def save_bookings(items):
    store_set(KEY_BOOKINGS, items)


def load_counters():
    return store_get(KEY_COUNTERS, {})


def save_counters(counters):
    store_set(KEY_COUNTERS, counters)


def next_booking_id(day_iso):
    counters = load_counters()
    seq = int(counters.get(day_iso, 0)) + 1
    counters[day_iso] = seq
    save_counters(counters)
    return f"SN-{day_iso.replace('-', '')}-{seq:03d}"


def find_user(email):
    target = (email or "").strip().lower()
    for user in load_users():
        if user.get("email", "").lower() == target:
            return user
    return None


def set_session(email):
    if email:
        store_set(KEY_SESSION, {"email": email.strip().lower()})
    else:
        store_del(KEY_SESSION)


def current_user():
    session = store_get(KEY_SESSION)
    if not session:
        return None
    user = find_user(session.get("email", ""))
    return user


def set_guest_email(email):
    if email:
        store_set(KEY_GUEST, email.strip().lower())


def guest_email():
    return store_get(KEY_GUEST, "")


def display_email():
    user = current_user()
    if user:
        return user.get("email", "")
    return guest_email() or ""


def register(name, email, phone, student_id, password):
    email = (email or "").strip().lower()
    if len((name or "").strip()) < 2:
        return False, "Please enter your full name."
    if "@" not in email or "." not in email.split("@")[-1] or len(email) < 6:
        return False, "Please enter a valid email address."
    if find_user(email):
        return False, "An account with that email already exists."
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if len(digits) < 10:
        return False, "Please enter a valid mobile number."
    if len((password or "")) < 6:
        return False, "Password must be at least 6 characters."
    users = load_users()
    users.append({
        "name": (name or "").strip(),
        "email": email,
        "phone": (phone or "").strip(),
        "student_id": (student_id or "").strip(),
        "password": password,
        "balance": 150.0,
        "joined": today_iso(),
    })
    save_users(users)
    set_session(email)
    return True, "Account created successfully."


def login(email, password):
    user = find_user(email or "")
    if not user:
        return False, "No account found with that email address."
    if user.get("password") != (password or ""):
        return False, "Incorrect password. Please try again."
    set_session(user["email"])
    return True, f"Welcome back, {user['name'].split(' ')[0]}!"


def logout():
    set_session(None)


def reset_password(email, new_password):
    users = load_users()
    target = (email or "").strip().lower()
    found = False
    for user in users:
        if user.get("email", "").lower() == target:
            user["password"] = new_password
            found = True
    if not found:
        return False, "No account found with that email address."
    if len((new_password or "")) < 6:
        return False, "Password must be at least 6 characters."
    save_users(users)
    return True, "Password updated. You can now log in."


def bookings_for(seat_id, day_iso):
    out = []
    for booking in load_bookings():
        if booking.get("seat") != seat_id:
            continue
        if booking.get("date") != day_iso:
            continue
        if booking.get("status") == "cancelled":
            continue
        out.append(booking)
    return out


def seat_state(seat_id, day_iso, slot, duration=1):
    for booking in bookings_for(seat_id, day_iso):
        if overlaps(slot, duration, booking.get("slot"), booking.get("duration", 1)):
            if booking.get("status") == "reserved":
                return "reserved"
            return "occupied"
    return "available"


def is_seat_free(seat_id, day_iso, slot, duration, ignore_id=None):
    for booking in bookings_for(seat_id, day_iso):
        if ignore_id and booking.get("id") == ignore_id:
            continue
        if overlaps(slot, duration, booking.get("slot"), booking.get("duration", 1)):
            return False
    return True


def seat_stats(day_iso, slot, duration=1):
    total = len(SEATS)
    occupied = 0
    reserved = 0
    available = 0
    for seat in SEATS:
        state = seat_state(seat["id"], day_iso, slot, duration)
        if state == "occupied":
            occupied += 1
        elif state == "reserved":
            reserved += 1
        else:
            available += 1
    return {"total": total, "available": available, "occupied": occupied, "reserved": reserved}


def slot_state(day_iso, slot):
    if day_iso == today_iso() and slot_hour(slot) < _now_hour():
        return "past"
    taken = 0
    for seat in SEATS:
        if seat_state(seat["id"], day_iso, slot, 1) != "available":
            taken += 1
    free = len(SEATS) - taken
    if free <= 0:
        return "full"
    if free <= 4:
        return "almost"
    return "available"


def slot_taken(day_iso, slot):
    taken = 0
    for seat in SEATS:
        if seat_state(seat["id"], day_iso, slot, 1) != "available":
            taken += 1
    return taken


def _now_hour():
    try:
        d = window.Date.new()
        return d.getHours() + d.getMinutes() / 60.0
    except Exception:
        return 0.0


def create_booking(payload):
    day_iso = payload.get("date")
    slot = payload.get("slot")
    duration = int(payload.get("duration", 1))
    seat_id = payload.get("seat")
    seat = SEAT_MAP.get(seat_id)

    if seat is None:
        return False, "Please select a study seat.", None
    if not day_iso:
        return False, "Please select a date.", None
    if slot not in TIME_SLOTS:
        return False, "Please select a time slot.", None
    if day_iso == today_iso() and slot_hour(slot) < _now_hour():
        return False, "That time slot has already passed today.", None
    if duration < 1 or duration > max_duration_for(slot):
        return False, "That duration runs past closing time.", None
    people = int(payload.get("people", 1) or 1)
    if people < 1 or people > seat["capacity"]:
        return False, f"{seat['label']} fits {seat['capacity']} {'person' if seat['capacity'] == 1 else 'people'}.", None
    if not is_seat_free(seat_id, day_iso, slot, duration):
        return False, "That seat was just booked for this time. Please pick another.", None
    name = (payload.get("name") or "").strip()
    if len(name) < 2:
        return False, "Please enter your full name.", None
    email = (payload.get("email") or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "Please enter a valid email address.", None
    digits = "".join(ch for ch in (payload.get("phone") or "") if ch.isdigit())
    if len(digits) < 10:
        return False, "Please enter a valid mobile number.", None

    rate = seat["rate"]
    subtotal = rate * duration
    printing = float(payload.get("printing", 0) or 0)
    snacks = float(payload.get("snacks", 0) or 0)
    total = subtotal + printing + snacks

    booking_id = next_booking_id(day_iso)
    booking = {
        "id": booking_id,
        "user_email": email,
        "name": name,
        "phone": (payload.get("phone") or "").strip(),
        "student_id": (payload.get("student_id") or "").strip(),
        "seat": seat_id,
        "kind": seat["kind"],
        "date": day_iso,
        "slot": slot,
        "duration": duration,
        "people": people,
        "rate": rate,
        "subtotal": subtotal,
        "printing": printing,
        "snacks": snacks,
        "total": total,
        "status": "confirmed",
        "created": today_iso(),
    }
    items = load_bookings()
    items.append(booking)
    save_bookings(items)
    set_guest_email(email)
    return True, "Booking confirmed.", booking


def get_booking(booking_id):
    for booking in load_bookings():
        if booking.get("id") == booking_id:
            return booking
    return None


def cancel_booking(booking_id):
    items = load_bookings()
    for booking in items:
        if booking.get("id") == booking_id:
            if booking.get("status") in ("cancelled", "completed"):
                return False, "This booking can no longer be changed."
            booking["status"] = "cancelled"
            save_bookings(items)
            return True, "Booking cancelled. The seat is free again."
    return False, "Booking not found."


def bookings_for_email(email):
    target = (email or "").strip().lower()
    if not target:
        return []
    items = [b for b in load_bookings() if b.get("user_email", "").lower() == target]
    items.sort(key=lambda b: (b.get("date", ""), b.get("slot", "")), reverse=True)
    return items


def split_bookings(items, day=None):
    day = day or today_iso()
    now = _now_hour()
    cancelled = []
    upcoming = []
    past = []
    for booking in items:
        if booking.get("status") == "cancelled":
            cancelled.append(booking)
            continue
        when = booking.get("date", "")
        end = slot_hour(booking.get("slot", "08:00")) + int(booking.get("duration", 1))
        if when < day or (when == day and end <= now):
            past.append(booking)
        else:
            upcoming.append(booking)
    upcoming.sort(key=lambda b: (b.get("date", ""), b.get("slot", "")))
    past.sort(key=lambda b: (b.get("date", ""), b.get("slot", "")), reverse=True)
    cancelled.sort(key=lambda b: (b.get("date", ""), b.get("slot", "")), reverse=True)
    return upcoming, past, cancelled


def upcoming_booking(email):
    items = bookings_for_email(email)
    upcoming, _, _ = split_bookings(items)
    return upcoming[0] if upcoming else None


def total_visits(email):
    items = bookings_for_email(email)
    _, past, _ = split_bookings(items)
    return len(past)


def receipt_text(booking):
    lines = [
        "=========================================",
        "              STUDYNEST                  ",
        "     Student Study Lounge Receipt        ",
        "=========================================",
        f"Booking ID : {booking['id']}",
        f"Name       : {booking['name']}",
        f"Email      : {booking['user_email']}",
        f"Date       : {fmt_date(booking['date'])}",
        f"Time       : {time_range(booking['slot'], booking['duration'])}",
        f"Seat       : {booking['seat']} ({SEAT_MAP[booking['seat']]['label']})",
        f"Rate       : {money(booking['rate'])}/hour",
        f"Duration   : {booking['duration']} hour(s)",
        f"People     : {booking['people']}",
        "-----------------------------------------",
        f"Subtotal   : {money2(booking['subtotal'])}",
        f"Printing   : {money2(booking['printing'])}",
        f"Snacks     : {money2(booking['snacks'])}",
        f"TOTAL      : {money2(booking['total'])}",
        "=========================================",
        "Open daily 8:00 AM - 10:00 PM",
        "Near campus main gate | (02) 8555-0142",
        "Thank you for studying with us!",
    ]
    return "\n".join(lines)


def _seed():
    if store_get(KEY_SEEDED):
        return

    demo_password = "studynest123"
    users = [
        {
            "name": "Maria Santos",
            "email": "maria@studynest.ph",
            "phone": "0917-421-8830",
            "student_id": "2026-00415",
            "password": demo_password,
            "balance": 150.0,
            "joined": "2026-08-14",
        },
        {
            "name": "Joy Ramirez",
            "email": "joy@studynest.ph",
            "phone": "0918-220-7741",
            "student_id": "2026-01188",
            "password": "joypassword",
            "balance": 60.0,
            "joined": "2026-09-02",
        },
    ]
    save_users(users)

    today = today_iso()
    bookings = []

    def add(bid, who, seat, when, slot, dur, people, status, rate=None):
        seat_info = SEAT_MAP[seat]
        rate = rate if rate is not None else seat_info["rate"]
        subtotal = rate * dur
        bookings.append({
            "id": bid,
            "user_email": who,
            "name": "",
            "phone": "",
            "student_id": "",
            "seat": seat,
            "kind": seat_info["kind"],
            "date": when,
            "slot": slot,
            "duration": dur,
            "people": people,
            "rate": rate,
            "subtotal": subtotal,
            "printing": 0.0,
            "snacks": 0.0,
            "total": float(subtotal),
            "status": status,
            "created": "2026-10-01",
        })

    add("SN-20261005-001", "joy@studynest.ph", "S07", "2026-10-05", "08:00", 3, 1, "completed")
    add("SN-20261005-002", "kiko@studynest.ph", "S11", "2026-10-05", "13:00", 2, 1, "completed")
    add("SN-20261005-003", "joy@studynest.ph", "G02", "2026-10-05", "15:00", 2, 5, "completed")
    add("SN-20261005-004", "maria@studynest.ph", "S03", "2026-10-05", "10:00", 2, 1, "completed", 25)

    add(f"SN-{today.replace('-', '')}-001", "joy@studynest.ph", "S01", today, "09:00", 2, 1, "confirmed")
    add(f"SN-{today.replace('-', '')}-002", "kiko@studynest.ph", "S04", today, "08:00", 3, 1, "confirmed")
    add(f"SN-{today.replace('-', '')}-003", "elena@studynest.ph", "S07", today, "10:00", 2, 1, "reserved")
    add(f"SN-{today.replace('-', '')}-004", "joy@studynest.ph", "S11", today, "11:00", 2, 1, "reserved")
    add(f"SN-{today.replace('-', '')}-005", "kiko@studynest.ph", "G01", today, "13:00", 3, 4, "confirmed")
    add(f"SN-{today.replace('-', '')}-006", "elena@studynest.ph", "S02", today, "14:00", 2, 1, "confirmed")
    add(f"SN-{today.replace('-', '')}-007", "joy@studynest.ph", "S05", today, "14:00", 2, 1, "confirmed")
    add(f"SN-{today.replace('-', '')}-008", "kiko@studynest.ph", "S09", today, "14:00", 1, 1, "reserved")
    add(f"SN-{today.replace('-', '')}-009", "elena@studynest.ph", "G03", today, "15:00", 2, 7, "confirmed")
    add(f"SN-{today.replace('-', '')}-010", "joy@studynest.ph", "S03", today, "16:00", 2, 1, "confirmed")

    tomorrow = (_date.fromisoformat(today) + _date.resolution).isoformat()
    add(f"SN-{tomorrow.replace('-', '')}-001", "kiko@studynest.ph", "S06", tomorrow, "09:00", 2, 1, "confirmed")
    add(f"SN-{tomorrow.replace('-', '')}-002", "elena@studynest.ph", "G01", tomorrow, "13:00", 3, 4, "reserved")

    add("SN-20261010-001", "maria@studynest.ph", "S05", "2026-10-10", "14:00", 2, 1, "confirmed", 25)

    save_bookings(bookings)

    counters = {
        "2026-10-05": 4,
        today: 10,
        tomorrow: 2,
        "2026-10-10": 1,
    }
    save_counters(counters)
    store_set(KEY_SEEDED, True)


def available_seats_for(day_iso, slot, duration):
    return [s for s in SEATS if is_seat_free(s["id"], day_iso, slot, duration)]


_seed()
