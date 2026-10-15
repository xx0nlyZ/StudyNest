import store
import ui


def current_slot():
    now_hour = 0
    try:
        d = ui.window.Date.new()
        now_hour = d.getHours() + d.getMinutes() / 60.0
    except Exception:
        now_hour = 0
    for slot in store.TIME_SLOTS:
        if store.slot_hour(slot) >= now_hour:
            return slot
    return store.TIME_SLOTS[-1]


def seat_chip(seat_id, state):
    label = {"available": "Available", "occupied": "Booked", "reserved": "Reserved"}.get(state, state)
    return (
        f'<span class="seat-chip {state}" title="{seat_id} \u00b7 {label}">'
        f'<span class="d"></span>{seat_id}</span>'
    )


def render_home():
    if ui.qs("#hero-live") is None:
        return

    today = store.today_iso()
    slot = current_slot()
    stats = store.seat_stats(today, slot)
    slot_state = store.slot_state(today, slot)

    state_class = {
        "available": "ok",
        "almost": "warn",
        "full": "bad",
        "past": "mute",
    }.get(slot_state, "ok")

    state_label = {
        "available": "Seats open",
        "almost": "Almost full",
        "full": "Fully booked",
        "past": "Slot passed",
    }.get(slot_state, "Seats open")

    ui.set_text(
        "#hero-slot-label",
        f"{store.fmt_date(today)} \u00b7 {store.slot_label(slot)} onwards",
    )

    rows = [
        ("status", state_label, f"{stats['available']} of {stats['total']} free", state_class),
        ("seats", "Available seats", str(stats["available"]), ""),
        ("seats", "Reserved seats", str(stats["reserved"]), ""),
        ("seats", "Occupied seats", str(stats["occupied"]), ""),
        ("hours", "Open today", "8:00 AM \u2013 10:00 PM", ""),
    ]

    html = ""
    for kind, key, value, cls in rows:
        dot = "dot-ok" if cls == "ok" else "dot-warn" if cls == "warn" else "dot-bad" if cls == "bad" else "dot-mute"
        if kind == "status":
            icon = f'<span class="status-dot {dot}"></span>'
        elif kind == "hours":
            icon = "<span class='status-dot dot-mute'></span>"
        else:
            icon = "<span class='status-dot dot-ok'></span>"
        html += (
            f'<div class="live-row"><span class="k">{icon}{key}</span>'
            f'<span class="v">{value}</span></div>'
        )
    ui.set_html("#hero-live", html)

    ui.set_text("#stat-total", stats["total"])
    ui.set_text("#stat-available", stats["available"])
    booked_today = len([b for b in store.load_bookings() if b.get("date") == today and b.get("status") != "cancelled"])
    ui.set_text("#stat-booked", booked_today)

    chips = ""
    for seat in store.SEATS:
        chips += seat_chip(seat["id"], store.seat_state(seat["id"], today, slot, 1))
    ui.set_html("#home-seats", chips)
    ui.set_text(
        "#home-floor-label",
        f"{stats['available']} seats free \u00b7 {store.slot_label(slot)}",
    )


def on_faq(e, target):
    item = target.parentNode if target.parentNode is not None else None
    if item is not None:
        item.classList.toggle("open")


def on_contact_submit(e, target):
    e.preventDefault()
    name = ui.get_value("#c-name")
    email = ui.get_value("#c-email")
    subject = ui.get_value("#c-subject")
    message = ui.get_value("#c-message")
    status = ui.qs("#form-status")

    errors = []
    if len(name) < 2:
        errors.append("your full name")
    if "@" not in email or "." not in email.split("@")[-1] or len(email) < 6:
        errors.append("a valid email address")
    if len(message) < 10:
        errors.append("a message of at least 10 characters")

    if errors:
        if status is not None:
            status.className = "form-status err"
            status.textContent = "Please enter " + "; ".join(errors) + "."
        ui.toast("Please complete the highlighted fields.", "err")
        return

    messages = store.store_get("sn.messages", [])
    messages.append({
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "date": store.today_iso(),
    })
    store.store_set("sn.messages", messages)

    if status is not None:
        status.className = "form-status ok"
        status.textContent = f"Thanks, {name.split(' ')[0]}! We will reply within 24 hours."
    ui.toast("Message sent to the StudyNest team.", "ok")
    for selector in ("#c-name", "#c-email", "#c-subject", "#c-message"):
        ui.set_value(selector, "")


def init():
    page = ui.current_page()
    ui.boot(page or "home")
    if page == "home":
        render_home()
        ui.window.setInterval(ui.proxy(render_home), 45000)
    if page == "pricing":
        ui.on(".faq-q", "click", on_faq)
    if page == "contact":
        ui.on("#contact-form", "submit", on_contact_submit)


init()
