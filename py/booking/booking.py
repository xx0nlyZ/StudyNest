from datetime import date, timedelta

from pyscript import window

import store
import ui

PRINTING_FEE = 20.0
SNACK_FEE = 25.0
MAX_LEAD_DAYS = 90

state = {
    "step": 1,
    "date": None,
    "slot": None,
    "seat": None,
    "duration": 1,
    "people": 1,
    "printing": 0.0,
    "snacks": 0.0,
    "cal_year": 2026,
    "cal_month": 1,
    "confirmed": None,
}


def days_in_month(year, month):
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]


def bounds():
    today = store.parse_iso(store.today_iso())
    return today, today + timedelta(days=MAX_LEAD_DAYS)


def init_calendar():
    today, _ = bounds()
    state["cal_year"] = today.year
    state["cal_month"] = today.month


def chosen_seat():
    if not state["seat"]:
        return None
    return store.SEAT_MAP.get(state["seat"])


def seat_rate():
    seat = chosen_seat()
    return seat["rate"] if seat else 0


def totals():
    subtotal = seat_rate() * int(state["duration"])
    return subtotal, state["printing"], state["snacks"], subtotal + state["printing"] + state["snacks"]


def render_stepper():
    for el in ui.qsa(".step-dot"):
        try:
            number = int(el.getAttribute("data-step"))
        except Exception:
            continue
        el.classList.toggle("is-active", number == state["step"])
        el.classList.toggle("is-done", number < state["step"])

    for number in range(1, 7):
        panel = ui.qs(f'.step-panel[data-panel="{number}"]')
        if panel is not None:
            panel.classList.toggle("hidden", number != state["step"])

    ui.set_text("#step-count", f"Step {state['step']} of 6")
    back = ui.qs("#step-back")
    if back is not None:
        back.disabled = state["step"] == 1
    nxt = ui.qs("#step-next")
    if nxt is not None:
        nxt.classList.toggle("hidden", state["step"] == 6)
        if state["step"] == 5:
            nxt.textContent = "Review booking \u2192"
        else:
            nxt.textContent = "Continue \u2192"


def render_calendar():
    year = state["cal_year"]
    month = state["cal_month"]
    ui.set_text("#cal-label", f"{store.MONTHS[month - 1]} {year}")

    first = date(year, month, 1)
    offset = (first.weekday() + 1) % 7
    total = days_in_month(year, month)
    today, last = bounds()
    selected = store.parse_iso(state["date"]) if state["date"] else None

    html = ""
    for _ in range(offset):
        html += '<span class="cal-day is-blank"></span>'
    for day in range(1, total + 1):
        current = date(year, month, day)
        disabled = current < today or current > last
        classes = ["cal-day"]
        if current == today:
            classes.append("is-today")
        if selected is not None and current == selected:
            classes.append("is-selected")
        iso = current.isoformat()
        flag = " disabled" if disabled else ""
        html += f'<button type="button" class="{" ".join(classes)}" data-date="{iso}"{flag}>{day}</button>'
    ui.set_html("#cal-grid", html)

    prev = ui.qs('.cal-nav-btn[data-dir="-1"]')
    nxt = ui.qs('.cal-nav-btn[data-dir="1"]')
    if prev is not None:
        prev.disabled = year == today.year and month == today.month
    if nxt is not None:
        nxt.disabled = year == last.year and month == last.month

    if state["date"]:
        ui.set_html("#date-chosen", f"{store.fmt_date(state['date'])}")
        open_slots = len([s for s in store.TIME_SLOTS if store.slot_state(state["date"], s) in ("available", "almost")])
        ui.set_html(
            "#date-hint",
            f'<span class="pill ok">{open_slots} of {len(store.TIME_SLOTS)} slots open</span>'
            f'<span class="pill navy">{store.slot_label(store.TIME_SLOTS[0])} &ndash; {store.slot_label(store.TIME_SLOTS[-1])}</span>',
        )
    else:
        ui.set_html("#date-chosen", "No date selected yet")
        ui.set_html("#date-hint", "")


def render_slots():
    if not state["date"]:
        return
    ui.set_text("#slot-context", f"Availability for {store.fmt_date(state['date'])} \u00b7 hourly slots 8:00 AM to 7:00 PM.")
    html = ""
    for slot in store.TIME_SLOTS:
        status = store.slot_state(state["date"], slot)
        cls = {
            "available": "is-available",
            "almost": "is-almost",
            "full": "is-full",
            "past": "is-past",
        }.get(status, "is-available")
        label = {
            "available": "Available",
            "almost": "Almost Full",
            "full": "Fully Booked",
            "past": "Passed",
        }.get(status, "Available")
        selected = " is-selected" if state["slot"] == slot else ""
        flag = " disabled" if status in ("full", "past") else ""
        html += (
            f'<button type="button" class="slot-card {cls}{selected}" data-slot="{slot}"{flag}>'
            f'<span class="t">{store.slot_label(slot)}</span>'
            f'<span class="s">{label}</span></button>'
        )
    ui.set_html("#slot-grid", html)

    if state["slot"]:
        ui.set_html(
            "#slot-chosen",
            f"{store.fmt_date(state['date'])} \u00b7 {store.time_range(state['slot'], state['duration'])}",
        )
        chosen = ui.qs("#slot-chosen")
        if chosen is not None:
            chosen.classList.remove("is-empty")
    else:
        ui.set_html("#slot-chosen", "No time selected yet")
        chosen = ui.qs("#slot-chosen")
        if chosen is not None:
            chosen.classList.add("is-empty")


def seat_button(seat):
    status = store.seat_state(seat["id"], state["date"], state["slot"], state["duration"])
    cls = {
        "available": "is-available",
        "reserved": "is-reserved",
        "occupied": "is-occupied",
    }.get(status, "is-available")
    if state["seat"] == seat["id"]:
        cls += " is-selected"
    flag = {"available": "\u25cf", "reserved": "\u25d1", "occupied": "\u25cf"}.get(status, "\u25cf")
    meta = f'{store.money(seat["rate"])}/hr \u00b7 {seat["zone"]}'
    return (
        f'<button type="button" class="seat {cls}" data-seat="{seat["id"]}" data-status="{status}">'
        f'<span class="seat-id">{seat["id"]}</span>'
        f'<span class="seat-meta">{meta}</span>'
        f'<span class="seat-flag">{flag}</span></button>'
    )


def render_floor():
    if not state["date"] or not state["slot"]:
        return
    ui.set_text(
        "#seat-context",
        f"{store.fmt_date(state['date'])} \u00b7 {store.time_range(state['slot'], state['duration'])} \u00b7 "
        f"tap a desk to select it.",
    )
    individual = [seat_button(s) for s in store.SEATS if s["kind"] == "individual"]
    group = [seat_button(s) for s in store.SEATS if s["kind"] == "group"]
    ui.set_html(
        "#floor-map",
        '<div class="floor">'
        '<div class="window-band">WINDOW</div>'
        f'<div class="floor-grid">{"".join(individual)}</div>'
        '<div class="group-band">GROUP STUDY AREA</div>'
        f'<div class="floor-grid">{"".join(group)}</div>'
        "</div>",
    )
    render_seat_detail()


def render_seat_detail():
    seat = chosen_seat()
    box = ui.qs("#seat-detail")
    if box is None:
        return
    if seat is None:
        ui.set_html(
            "#seat-detail",
            '<p class="side-note">Nothing selected yet. Green desks on the floor plan are free for your chosen date and time.</p>',
        )
        return
    kind = "Group table" if seat["kind"] == "group" else "Individual seat"
    chips = "".join(f'<span class="chip">{ui.esc(a)}</span>' for a in seat["amenities"])
    ui.set_html(
        "#seat-detail",
        f'<div class="row mb-2"><span class="pill navy">{seat["id"]}</span>'
        f'<span class="pill ok">Selected</span></div>'
        f'<p class="side-value">{ui.esc(seat["label"])}</p>'
        '<div class="detail-rows">'
        f'<div class="detail-row"><span>Type</span><strong>{kind}</strong></div>'
        f'<div class="detail-row"><span>Location</span><strong>{ui.esc(seat["zone"])}</strong></div>'
        f'<div class="detail-row"><span>Rate</span><strong>{store.money(seat["rate"])}/hour</strong></div>'
        f'<div class="detail-row"><span>Fits</span><strong>{"1 student" if seat["capacity"] == 1 else str(seat["capacity"]) + " students"}</strong></div>'
        '<div class="detail-row"><span>Status</span><strong>Available</strong></div>'
        "</div>"
        f'<div class="chip-row">{chips}</div>',
    )


def render_durations():
    if not state["slot"]:
        return
    cap = store.max_duration_for(state["slot"])
    seat = chosen_seat()
    html = ""
    for hours in range(1, 6):
        locked = hours > cap
        selected = " is-selected" if state["duration"] == hours else ""
        flag = " disabled" if locked else ""
        price = store.money(seat["rate"] * hours) if seat else store.money(0)
        html += (
            f'<button type="button" class="dur-card{selected}" data-duration="{hours}"{flag}>'
            f'<span class="n">{hours}</span>'
            f'<span class="u">{"Hour" if hours == 1 else "Hours"}</span>'
            f'<span class="p">{price}</span></button>'
        )
    ui.set_html("#duration-grid", html)
    render_price()


def render_price():
    seat = chosen_seat()
    if seat is None:
        ui.set_html("#price-preview", "")
        return
    subtotal, printing, snacks, total = totals()
    ui.set_html(
        "#price-preview",
        '<div class="lines">'
        f'<span>Seat <strong>{seat["id"]} \u00b7 {ui.esc(seat["zone"])}</strong></span>'
        f'<span><strong>{store.money(seat["rate"])}</strong> / hour &times; <strong>{state["duration"]}</strong> '
        f'{"hour" if state["duration"] == 1 else "hours"}</span>'
        "</div>"
        f'<div class="total">{store.money(total)}<br><small>total due at the counter</small></div>',
    )


def render_summary():
    seat = chosen_seat()
    if seat is None or not state["slot"] or not state["date"]:
        return
    subtotal, printing, snacks, total = totals()
    ui.set_html(
        "#summary",
        '<div class="summary-title">Booking Summary</div>'
        f'<div class="sum-row"><span>Date</span><strong>{store.fmt_date(state["date"])}</strong></div>'
        f'<div class="sum-row"><span>Time</span><strong>{store.slot_label(state["slot"])} \u2013 {store.slot_end_label(state["slot"], state["duration"])}</strong></div>'
        f'<div class="sum-row"><span>Duration</span><strong>{state["duration"]} {"Hour" if state["duration"] == 1 else "Hours"}</strong></div>'
        f'<div class="sum-row"><span>Seat</span><strong>{seat["id"]} \u00b7 {ui.esc(seat["label"])}</strong></div>'
        f'<div class="sum-row"><span>People</span><strong>{state["people"]}</strong></div>'
        f'<div class="sum-row"><span>Rate</span><strong>{store.money(seat["rate"])}/hour</strong></div>'
        f'<div class="sum-row"><span>Subtotal</span><strong>{store.money(subtotal)}</strong></div>'
        f'<div class="sum-row{" muted-row" if printing == 0 else ""}"><span>Printing</span><strong>{store.money2(printing)}</strong></div>'
        f'<div class="sum-row{" muted-row" if snacks == 0 else ""}"><span>Snacks</span><strong>{store.money2(snacks)}</strong></div>'
        f'<div class="sum-row total"><span>TOTAL</span><strong>{store.money2(total)}</strong></div>',
    )


def render_info():
    seat = chosen_seat()
    if seat is None:
        return
    capacity = seat["capacity"]
    people = ui.qs("#b-people")
    if people is not None:
        people.max = str(capacity)
    ui.set_html(
        "#info-seat",
        f'{seat["id"]} \u00b7 {ui.esc(seat["label"])} &mdash; {store.money(seat["rate"])}/hour, fits '
        f'{"1 student" if capacity == 1 else str(capacity) + " students"}.',
    )
    hint = ui.qs("#people-hint")
    if hint is not None:
        hint.textContent = (
            "Individual seats fit 1 student."
            if capacity == 1
            else f"This group table seats up to {capacity} students."
        )


def render_all():
    render_stepper()
    if state["step"] == 1:
        render_calendar()
    if state["step"] == 2:
        render_slots()
    if state["step"] == 3:
        render_floor()
    if state["step"] == 4:
        render_durations()
    if state["step"] == 5:
        render_info()
    if state["step"] == 6:
        render_summary()


def goto(step):
    state["step"] = max(1, min(6, step))
    if state["step"] == 1:
        render_calendar()
    if state["step"] == 2:
        render_slots()
    if state["step"] == 3:
        render_floor()
    if state["step"] == 4:
        render_durations()
    if state["step"] == 5:
        render_info()
    if state["step"] == 6:
        render_summary()
    render_stepper()
    body = ui.qs(".wizard-body")
    if body is not None:
        try:
            top = (body.getBoundingClientRect().top or 0) + float(window.scrollY or 0) - 96
            window.scrollTo(0, top)
        except Exception:
            pass


def set_error(field, message):
    box = ui.qs(f"#e-{field}")
    if box is not None:
        box.textContent = message
    control = ui.qs(f"#b-{field}")
    if control is not None:
        control.classList.toggle("invalid", bool(message))


def validate_info():
    name = ui.get_value("#b-name")
    email = ui.get_value("#b-email")
    phone = ui.get_value("#b-phone")
    student_id = ui.get_value("#b-sid")
    people_raw = ui.get_value("#b-people", "1")
    seat = chosen_seat()
    errors = []

    set_error("name", "")
    set_error("email", "")
    set_error("phone", "")
    set_error("people", "")

    if len(name) < 2:
        set_error("name", "Enter your full name.")
        errors.append("full name")
    if "@" not in email or "." not in email.split("@")[-1] or len(email) < 6:
        set_error("email", "Enter a valid email address.")
        errors.append("valid email")
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 10:
        set_error("phone", "Enter a valid mobile number.")
        errors.append("mobile number")

    try:
        people = int(float(people_raw))
    except Exception:
        people = 0
    capacity = seat["capacity"] if seat else 1
    if people < 1 or people > capacity:
        set_error("people", f"Allowed: 1 to {capacity}.")
        errors.append("number of people")
        people = 1
    state["people"] = people

    alert = ui.qs("#form-alert")
    if errors:
        if alert is not None:
            alert.classList.remove("hidden")
            alert.textContent = "Please fix: " + ", ".join(errors) + "."
        ui.toast("Please complete your details.", "err")
        return None
    if alert is not None:
        alert.classList.add("hidden")
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "student_id": student_id,
        "people": people,
    }


def on_next(_e, _t):
    step = state["step"]
    if step == 1 and not state["date"]:
        ui.toast("Pick a date first.", "warn")
        return
    if step == 2 and not state["slot"]:
        ui.toast("Pick a time slot first.", "warn")
        return
    if step == 3 and not state["seat"]:
        ui.toast("Select a study seat.", "warn")
        return
    if step == 5 and validate_info() is None:
        return
    goto(step + 1)


def on_back(_e, _t):
    if state["step"] > 1:
        goto(state["step"] - 1)


def on_step_dot(e, target):
    try:
        number = int(target.getAttribute("data-step"))
    except Exception:
        return
    if number < state["step"]:
        goto(number)


def on_month(e, target):
    direction = int(target.getAttribute("data-dir"))
    month = state["cal_month"] + direction
    year = state["cal_year"]
    if month < 1:
        month = 12
        year -= 1
    if month > 12:
        month = 1
        year += 1
    _, last = bounds()
    if date(year, month, 1) > last:
        return
    today, _ = bounds()
    if date(year, month, days_in_month(year, month)) < today:
        return
    state["cal_month"] = month
    state["cal_year"] = year
    render_calendar()


def on_day(e, target):
    value = target.getAttribute("data-date")
    if not value:
        return
    today, last = bounds()
    chosen = store.parse_iso(value)
    if chosen < today or chosen > last:
        return
    if state["date"] != value:
        state["date"] = value
        if state["slot"] and store.slot_state(value, state["slot"]) == "past":
            state["slot"] = None
        if state["seat"] and not store.is_seat_free(state["seat"], value, state["slot"] or store.TIME_SLOTS[0], state["duration"]):
            state["seat"] = None
    render_calendar()
    ui.toast(f"Date set: {store.fmt_date(value)}", "ok")


def on_slot(e, target):
    value = target.getAttribute("data-slot")
    if not value or not state["date"]:
        return
    if store.slot_state(state["date"], value) in ("full", "past"):
        ui.toast("That slot is not bookable.", "err")
        return
    if state["slot"] == value:
        return
    state["slot"] = value
    cap = store.max_duration_for(value)
    if state["duration"] > cap:
        state["duration"] = max(1, cap)
    if state["seat"] and not store.is_seat_free(state["seat"], state["date"], value, state["duration"]):
        state["seat"] = None
        ui.toast("That seat is taken for the new time. Pick another desk.", "warn")
    render_slots()
    if state["seat"]:
        ui.set_text(
            "#slot-chosen",
            f"{store.fmt_date(state['date'])} \u00b7 {store.time_range(state['slot'], state['duration'])}",
        )


def on_seat(e, target):
    value = target.getAttribute("data-seat")
    status = target.getAttribute("data-status")
    if not value:
        return
    if status in ("occupied", "reserved"):
        ui.toast(f"{value} is already booked for this time.", "err")
        return
    state["seat"] = value
    seat = store.SEAT_MAP[value]
    state["people"] = 1
    render_floor()
    ui.toast(f"{value} selected \u00b7 {store.money(seat['rate'])}/hour", "ok")


def on_duration(e, target):
    try:
        hours = int(target.getAttribute("data-duration"))
    except Exception:
        return
    if not state["slot"] or hours > store.max_duration_for(state["slot"]):
        return
    state["duration"] = hours
    if state["seat"] and not store.is_seat_free(state["seat"], state["date"], state["slot"], hours):
        state["seat"] = None
        ui.toast("That desk is taken for a longer session. Choose another seat.", "warn")
        goto(3)
        return
    render_durations()


def on_addon(e, target):
    checked = bool(getattr(target, "checked", False))
    if target.id == "add-printing":
        state["printing"] = PRINTING_FEE if checked else 0.0
    if target.id == "add-snacks":
        state["snacks"] = SNACK_FEE if checked else 0.0
    render_summary()


def on_people(e, target):
    try:
        value = int(float(str(target.value)))
    except Exception:
        value = 1
    state["people"] = max(1, value)


def submit():
    payload = validate_info()
    if payload is None:
        goto(5)
        return
    payload["date"] = state["date"]
    payload["slot"] = state["slot"]
    payload["duration"] = state["duration"]
    payload["seat"] = state["seat"]
    payload["printing"] = state["printing"]
    payload["snacks"] = state["snacks"]
    ok, message, booking = store.create_booking(payload)
    if not ok:
        alert = ui.qs("#form-alert")
        if alert is not None:
            alert.classList.remove("hidden")
            alert.textContent = message
        ui.toast(message, "err")
        state["seat"] = None
        goto(3)
        return
    state["confirmed"] = booking
    show_confirmation(booking)


def on_confirm(_e, _t):
    submit()


def show_confirmation(booking):
    seat = store.SEAT_MAP[booking["seat"]]
    ui.set_html(
        "#confirm-view",
        '<div class="confirm-mark">&#10003;</div>'
        "<h2>Booking Confirmed</h2>"
        '<p class="lead">Your seat is locked in. Show this booking ID at the counter when you arrive.</p>'
        f'<div class="confirm-id">{booking["id"]}</div>'
        '<div class="confirm-grid">'
        f'<div class="confirm-cell"><span class="k">Seat</span><span class="v">{booking["seat"]} \u00b7 {ui.esc(seat["zone"])}</span></div>'
        f'<div class="confirm-cell"><span class="k">Date</span><span class="v">{store.fmt_date(booking["date"])}</span></div>'
        f'<div class="confirm-cell"><span class="k">Time</span><span class="v">{store.time_range(booking["slot"], booking["duration"])}</span></div>'
        f'<div class="confirm-cell"><span class="k">Duration</span><span class="v">{booking["duration"]} {"Hour" if booking["duration"] == 1 else "Hours"}</span></div>'
        f'<div class="confirm-cell"><span class="k">Rate</span><span class="v">{store.money(booking["rate"])}/hour</span></div>'
        f'<div class="confirm-cell"><span class="k">People</span><span class="v">{booking["people"]}</span></div>'
        f'<div class="confirm-cell"><span class="k">Name</span><span class="v">{ui.esc(booking["name"])}</span></div>'
        f'<div class="confirm-cell"><span class="k">Total</span><span class="v">{store.money2(booking["total"])}</span></div>'
        "</div>"
        '<div class="confirm-actions">'
        f'<a href="{ui.url("my-bookings.html")}" class="btn btn-primary">View My Booking</a>'
        f'<button type="button" class="btn btn-ghost" id="dl-receipt" data-bid="{booking["id"]}">Download Receipt</button>'
        '<button type="button" class="btn btn-amber" id="book-again">Book Another Seat</button>'
        "</div>",
    )
    ui.qs("#wizard").classList.add("hidden")
    ui.qs("#confirm-view").classList.remove("hidden")
    ui.toast(f"Booking {booking['id']} confirmed!", "ok")
    try:
        top = (ui.qs("#confirm-view").getBoundingClientRect().top or 0) + float(window.scrollY or 0) - 96
        window.scrollTo(0, top)
    except Exception:
        pass


def on_receipt(e, target):
    booking_id = target.getAttribute("data-bid")
    booking = store.get_booking(booking_id)
    if booking:
        ui.download_text(f"{booking_id}.txt", store.receipt_text(booking))
        ui.toast("Receipt downloaded.", "ok")


def on_reset(_e, _t):
    state.update({
        "step": 1,
        "date": None,
        "slot": None,
        "seat": None,
        "duration": 1,
        "people": 1,
        "printing": 0.0,
        "snacks": 0.0,
        "confirmed": None,
    })
    for selector in ("#add-printing", "#add-snacks"):
        box = ui.qs(selector)
        if box is not None:
            box.checked = False
    init_calendar()
    ui.set_html("#confirm-view", "")
    ui.qs("#confirm-view").classList.add("hidden")
    ui.qs("#wizard").classList.remove("hidden")
    prefill()
    goto(1)
    ui.toast("Fresh start — pick a new date.", "ok")


def prefill():
    user = store.current_user()
    if not user:
        return
    ui.set_value("#b-name", user.get("name", ""))
    ui.set_value("#b-email", user.get("email", ""))
    ui.set_value("#b-phone", user.get("phone", ""))
    ui.set_value("#b-sid", user.get("student_id", ""))


def apply_deep_link():
    day = ui.param("date")
    slot = ui.param("time")
    seat = ui.param("seat")
    today, last = bounds()

    if day:
        try:
            chosen = store.parse_iso(day)
        except Exception:
            chosen = None
        if chosen is not None and today <= chosen <= last:
            state["date"] = day
            state["cal_year"] = chosen.year
            state["cal_month"] = chosen.month

    if slot and slot in store.TIME_SLOTS and state["date"]:
        if store.slot_state(state["date"], slot) not in ("full", "past"):
            state["slot"] = slot

    if seat and seat in store.SEAT_MAP and state["date"] and state["slot"]:
        if store.is_seat_free(seat, state["date"], state["slot"], state["duration"]):
            state["seat"] = seat
            return 4

    if state["date"] and state["slot"]:
        return 3
    if state["date"]:
        return 2
    return 1


def init():
    ui.boot("book")
    init_calendar()
    prefill()
    step = apply_deep_link()

    ui.on(".cal-nav-btn", "click", on_month)
    ui.on(".cal-day", "click", on_day)
    ui.on(".slot-card", "click", on_slot)
    ui.on(".seat", "click", on_seat)
    ui.on(".dur-card", "click", on_duration)
    ui.on(".step-dot", "click", on_step_dot)
    ui.on("#step-next", "click", on_next)
    ui.on("#step-back", "click", on_back)
    ui.on("#confirm-book", "click", on_confirm)
    ui.on("#dl-receipt", "click", on_receipt)
    ui.on("#book-again", "click", on_reset)
    ui.on("#add-printing", "change", on_addon)
    ui.on("#add-snacks", "change", on_addon)
    ui.on("#b-people", "input", on_people)

    goto(step)
    if state["seat"]:
        ui.toast("Seat preselected from the availability page.", "ok")


init()
