import store
import ui

state = {"tab": "upcoming"}

EMPTY_COPY = {
    "upcoming": (
        "No upcoming bookings",
        "Reserve a desk and your next session will show up here.",
    ),
    "past": (
        "No past visits yet",
        "Once a session finishes it moves here with its receipt.",
    ),
    "cancelled": (
        "Nothing cancelled",
        "If you ever cancel a reservation it will be listed here.",
    ),
}


def now_hour():
    try:
        d = ui.window.Date.new()
        return d.getHours() + d.getMinutes() / 60.0
    except Exception:
        return 0.0


def current_slot():
    hour = now_hour()
    for slot in store.TIME_SLOTS:
        if store.slot_hour(slot) >= hour:
            return slot
    return store.TIME_SLOTS[-1]


def status_pill(status):
    if status == "confirmed":
        return "ok", "Confirmed"
    if status == "cancelled":
        return "bad", "Cancelled"
    if status == "reserved":
        return "warn", "Reserved"
    if status == "completed":
        return "mute", "Completed"
    return "mute", str(status).capitalize()


def rows_html(rows):
    return "".join(
        f'<div class="detail-row"><span>{ui.esc(key)}</span><strong>{ui.esc(value)}</strong></div>'
        for key, value in rows
    )


def empty_block(title, copy, button=""):
    actions = ""
    if button:
        actions = f'<div class="empty-actions">{button}</div>'
    return (
        '<div class="empty-state">'
        f"<h4>{ui.esc(title)}</h4>"
        f"<p>{ui.esc(copy)}</p>"
        f"{actions}"
        "</div>"
    )


def on_tab(_e, target):
    chosen = target.getAttribute("data-tab") or "upcoming"
    state["tab"] = chosen
    for tab in ui.qsa("[data-tab]"):
        if tab.getAttribute("data-tab") == chosen:
            tab.classList.add("active")
        else:
            tab.classList.remove("active")
    render_bookings()


def on_view(_e, target):
    bid = target.getAttribute("data-view") or ""
    booking = store.get_booking(bid)
    if booking is None:
        ui.toast("That booking could not be found.", "err")
        return

    seat = store.SEAT_MAP.get(booking.get("seat", ""), {})
    _cls, label = status_pill(booking.get("status", ""))
    rows = [
        ("Booking ID", booking.get("id", "")),
        ("Status", label),
        ("Date", store.fmt_date(booking.get("date"))),
        ("Time", store.time_range(booking.get("slot", "08:00"), booking.get("duration", 1))),
        ("Seat", f"{booking.get('seat', '')} \u00b7 {seat.get('label', '')}"),
        ("Type", "Group" if booking.get("kind") == "group" else "Individual"),
        ("People", str(booking.get("people", 1))),
        ("Duration", f"{booking.get('duration', 1)} hour(s)"),
        ("Rate", f"{store.money(booking.get('rate', 0))}/hour"),
        ("Subtotal", store.money2(booking.get("subtotal", 0))),
        ("Printing", store.money2(booking.get("printing", 0))),
        ("Snacks", store.money2(booking.get("snacks", 0))),
        ("Total", store.money2(booking.get("total", 0))),
        ("Name", booking.get("name") or "\u2014"),
        ("Email", booking.get("user_email") or "\u2014"),
        ("Phone", booking.get("phone") or "\u2014"),
        ("Student ID", booking.get("student_id") or "\u2014"),
    ]
    html = (
        f'<div class="detail-rows">{rows_html(rows)}</div>'
        '<div class="m-actions">'
        '<button type="button" class="btn btn-ghost btn-sm" data-modal-close="1">Close</button>'
        f'<button type="button" class="btn btn-primary btn-sm" data-receipt="{booking.get("id", "")}">'
        "Download receipt</button>"
        "</div>"
    )
    ui.open_modal(html, f"Booking {booking.get('id', '')}")


def on_receipt(_e, target):
    bid = target.getAttribute("data-receipt") or ""
    booking = store.get_booking(bid)
    if booking is None:
        ui.toast("That booking could not be found.", "err")
        return
    ui.download_text(f"{bid}.txt", store.receipt_text(booking))
    ui.toast("Receipt downloaded.", "ok")


def do_cancel(bid):
    ok, message = store.cancel_booking(bid)
    ui.toast(message, "ok" if ok else "err")
    render_bookings()


def on_cancel(_e, target):
    bid = target.getAttribute("data-cancel") or ""
    if not bid:
        return
    ui.confirm_dialog(
        "Cancel this booking?",
        "The seat is released right away and you can book it again later.",
        "Cancel booking",
        lambda: do_cancel(bid),
    )


def booking_card(booking, tab):
    seat = store.SEAT_MAP.get(booking.get("seat", ""), {})
    cls, label = status_pill(booking.get("status", ""))
    bid = booking.get("id", "")
    kind = "Group" if booking.get("kind") == "group" else "Individual"
    people = int(booking.get("people", 1) or 1)
    unit = "person" if people == 1 else "people"

    if tab == "upcoming" and booking.get("status") != "cancelled":
        actions = (
            f'<button type="button" class="btn btn-ghost btn-sm" data-view="{bid}">View details</button>'
            f'<button type="button" class="btn btn-danger btn-sm" data-cancel="{bid}">Cancel</button>'
        )
    else:
        actions = (
            f'<button type="button" class="btn btn-ghost btn-sm" data-view="{bid}">View details</button>'
            f'<button type="button" class="btn btn-primary btn-sm" data-receipt="{bid}">Download receipt</button>'
        )

    return (
        '<article class="card booking-card">'
        '<div class="grid grid-2 booking-grid">'
        '<div class="booking-when">'
        '<div class="booking-head">'
        f'<span class="pill navy">{ui.esc(bid)}</span>'
        f'<span class="pill {cls}">{ui.esc(label)}</span>'
        "</div>"
        f"<h3>{ui.esc(booking.get('seat', ''))} \u00b7 {ui.esc(seat.get('label', ''))}</h3>"
        f'<p class="muted">{ui.esc(kind)} &middot; {ui.esc(str(people))} {unit} '
        f'&middot; {ui.esc(store.slot_label(booking.get("slot", "08:00")))}</p>'
        "</div>"
        '<div class="booking-facts">'
        f'<div class="fact-row"><span>Date</span><strong>{ui.esc(store.fmt_date(booking.get("date")))}</strong></div>'
        f'<div class="fact-row"><span>Time</span><strong>{ui.esc(store.time_range(booking.get("slot", "08:00"), booking.get("duration", 1)))}</strong></div>'
        f'<div class="fact-row"><span>Total</span><strong>{ui.esc(store.money(booking.get("total", 0)))}</strong></div>'
        f'<div class="booking-actions">{actions}</div>'
        "</div>"
        "</div>"
        "</article>"
    )


def render_bookings():
    email = store.display_email()
    gate = ui.qs("#bookings-gate")
    shell = ui.qs("#bookings-shell")

    if not email:
        if gate is not None:
            gate.classList.remove("hidden")
        if shell is not None:
            shell.classList.add("hidden")
        return

    if gate is not None:
        gate.classList.add("hidden")
    if shell is not None:
        shell.classList.remove("hidden")

    ui.set_text("#bookings-email", email)

    upcoming, past, cancelled = store.split_bookings(store.bookings_for_email(email))
    ui.set_text("#count-upcoming", len(upcoming))
    ui.set_text("#count-past", len(past))
    ui.set_text("#count-cancelled", len(cancelled))

    groups = {"upcoming": upcoming, "past": past, "cancelled": cancelled}
    rows = groups.get(state["tab"], upcoming)

    if not rows:
        title, copy = EMPTY_COPY.get(state["tab"], EMPTY_COPY["upcoming"])
        ui.set_html("#booking-list", f'<div class="card">{empty_block(title, copy)}</div>')
        return

    ui.set_html(
        "#booking-list",
        "".join(booking_card(booking, state["tab"]) for booking in rows),
    )


def setup_bookings():
    ui.on("[data-tab]", "click", on_tab)
    ui.on("[data-view]", "click", on_view)
    ui.on("[data-cancel]", "click", on_cancel)
    ui.on("[data-receipt]", "click", on_receipt)
    render_bookings()


def recent_row(booking):
    seat = store.SEAT_MAP.get(booking.get("seat", ""), {})
    cls, label = status_pill(booking.get("status", ""))
    when = f"{store.fmt_date(booking.get('date'))} \u00b7 {store.slot_label(booking.get('slot', '08:00'))}"
    return (
        '<div class="recent-row">'
        f'<span class="pill navy">{ui.esc(booking.get("id", ""))}</span>'
        f'<span class="r-seat">{ui.esc(booking.get("seat", ""))} &middot; {ui.esc(seat.get("label", ""))}</span>'
        f'<span class="r-when">{ui.esc(when)}</span>'
        f'<span class="pill {cls}">{ui.esc(label)}</span>'
        f'<a href="{ui.url("my-bookings.html")}" class="btn btn-ghost btn-sm">View</a>'
        "</div>"
    )


def render_recent(email):
    rows = store.bookings_for_email(email)[:4]
    if not rows:
        ui.set_html(
            "#recent-list",
            empty_block(
                "No bookings yet",
                "Your reserved sessions will appear here.",
                f'<a href="{ui.url("booking.html")}" class="btn btn-primary btn-sm">Book a seat</a>',
            ),
        )
        return
    ui.set_html("#recent-list", "".join(recent_row(booking) for booking in rows))


def render_dashboard(user):
    name = user.get("name", "")
    parts = name.split()
    first = parts[0] if parts else "there"
    initials = "".join([part[0] for part in parts[:2]]).upper() or "SN"
    email = user.get("email", "")
    joined = user.get("joined") or store.today_iso()

    ui.set_text("#dash-title", f"Welcome back, {first}")
    ui.set_text("#dash-sub", f"{email} \u00b7 Member since {store.fmt_date(joined)}")
    ui.set_text("#dash-avatar", initials)

    upcoming = store.upcoming_booking(email)
    upcoming_value = ui.qs("#kpi-upcoming")
    if upcoming_value is not None:
        upcoming_value.classList.toggle("sm", upcoming is None)
    if upcoming:
        ui.set_text("#kpi-upcoming", upcoming.get("seat", ""))
        ui.set_text(
            "#kpi-upcoming-label",
            f"{store.fmt_date(upcoming.get('date'))} \u00b7 {store.slot_label(upcoming.get('slot', '08:00'))}",
        )
    else:
        ui.set_text("#kpi-upcoming", "No booking yet")
        ui.set_text("#kpi-upcoming-label", "Upcoming booking")

    stats = store.seat_stats(store.today_iso(), current_slot())
    ui.set_text("#kpi-seats", stats["available"])
    ui.set_text("#kpi-balance", store.money2(user.get("balance", 0)))
    ui.set_text("#kpi-visits", store.total_visits(email))

    render_recent(email)
    ui.paint_status()


def setup_dashboard():
    user = store.current_user()
    gate = ui.qs("#dash-gate")
    shell = ui.qs("#dash-shell")

    if user is None:
        if gate is not None:
            gate.classList.remove("hidden")
        if shell is not None and shell.parentNode is not None:
            shell.parentNode.removeChild(shell)
        return

    if gate is not None and gate.parentNode is not None:
        gate.parentNode.removeChild(gate)
    if shell is not None:
        shell.classList.remove("hidden")
    render_dashboard(user)


def init():
    page = ui.current_page()
    ui.boot(page)
    if page == "my-bookings":
        setup_bookings()
    if page == "dashboard":
        setup_dashboard()


init()
