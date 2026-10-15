import store
import ui

state = {"date": "", "slot": "", "filter": "all", "selected": ""}


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


def seat_matches(seat, seat_state):
    chosen = state["filter"]
    if chosen == "available":
        return seat_state == "available"
    if chosen == "occupied":
        return seat_state == "occupied"
    if chosen == "group":
        return seat["kind"] == "group"
    if chosen == "individual":
        return seat["kind"] == "individual"
    return True


def seat_html(seat, seat_state):
    classes = ["seat", "is-" + seat_state]
    if state["selected"] == seat["id"]:
        classes.append("is-selected")
    if not seat_matches(seat, seat_state):
        classes.append("is-dim")
    meta = f"{store.PESO}{seat['rate']}/hr \u00b7 {seat['zone']}"
    return (
        f'<button type="button" class="{" ".join(classes)}" data-seat="{seat["id"]}">'
        f'<span class="seat-id">{seat["id"]}</span>'
        f'<span class="seat-meta">{ui.esc(meta)}</span>'
        '<span class="seat-flag">\u25cf</span>'
        "</button>"
    )


def render_floor():
    individual = ""
    group = ""
    shown = 0
    for seat in store.SEATS:
        seat_state = store.seat_state(seat["id"], state["date"], state["slot"], 1)
        if seat_matches(seat, seat_state):
            shown += 1
        block = seat_html(seat, seat_state)
        if seat["kind"] == "group":
            group += block
        else:
            individual += block
    ui.set_html(
        "#floor-map",
        (
            '<div class="floor">'
            '<div class="window-band">WINDOW</div>'
            f'<div class="floor-grid">{individual}</div>'
            '<div class="group-band">GROUP STUDY AREA</div>'
            f'<div class="floor-grid">{group}</div>'
            "</div>"
        ),
    )
    note = ui.qs("#filter-empty")
    if note is not None:
        note.classList.toggle("hidden", shown > 0)


def render_stats():
    stats = store.seat_stats(state["date"], state["slot"])
    ui.set_text("#kpi-total", stats["total"])
    ui.set_text("#kpi-available", stats["available"])
    ui.set_text("#kpi-occupied", stats["occupied"])
    ui.set_text("#kpi-reserved", stats["reserved"])
    ui.set_text(
        "#seats-context",
        f"{store.fmt_date(state['date'])} \u00b7 {store.slot_label(state['slot'])}",
    )


def empty_detail():
    return (
        '<div class="empty-state">'
        '<div class="big">\U0001fa91</div>'
        "<h4>Pick a seat</h4>"
        "<p>Tap any desk on the floor plan to see its rate, amenities and live status.</p>"
        "</div>"
    )


def render_detail():
    seat = store.SEAT_MAP.get(state["selected"])
    if seat is None:
        ui.set_html("#seat-detail", empty_detail())
        return

    seat_state = store.seat_state(seat["id"], state["date"], state["slot"], 1)
    pill = {"available": "ok", "reserved": "warn", "occupied": "bad"}.get(seat_state, "mute")
    kind = "Group" if seat["kind"] == "group" else "Individual"
    capacity = int(seat["capacity"])
    unit = "person" if capacity == 1 else "people"
    chips = "".join(f'<span class="chip">{ui.esc(a)}</span>' for a in seat["amenities"])
    when = f"{store.fmt_date(state['date'])} \u00b7 {store.slot_label(state['slot'])}"
    href = f"{ui.url('booking.html')}?seat={seat['id']}&date={state['date']}&time={state['slot']}"

    rows = [
        ("Type", kind),
        ("Zone", seat["zone"]),
        ("Rate", f"{store.money(seat['rate'])}/hour"),
        ("Capacity", f"{capacity} {unit}"),
        ("When", when),
    ]
    rows_html = "".join(
        f'<div class="detail-row"><span>{ui.esc(key)}</span><strong>{ui.esc(value)}</strong></div>'
        for key, value in rows
    )

    note = ""
    if seat_state != "available":
        note = (
            f'<p class="muted mt-2">This seat is {ui.esc(seat_state)} for the slot above. '
            "Open the booking page to try another hour or another desk.</p>"
        )

    ui.set_html(
        "#seat-detail",
        (
            '<div class="row between mb-2">'
            f"<h3>{ui.esc(seat['id'])} \u00b7 {ui.esc(seat['label'])}</h3>"
            f'<span class="pill {pill}">{ui.esc(seat_state.capitalize())}</span>'
            "</div>"
            f'<div class="detail-rows">{rows_html}</div>'
            '<p class="detail-sub">Amenities</p>'
            f'<div class="chip-row">{chips}</div>'
            f"{note}"
            f'<a class="btn btn-primary btn-block mt-3" href="{href}">Book this seat</a>'
        ),
    )


def render():
    render_stats()
    render_floor()
    render_detail()


def on_date(_e, _target):
    value = ui.get_value("#seat-date") or store.today_iso()
    state["date"] = value
    render()


def on_slot(_e, _target):
    value = ui.get_value("#seat-slot") or store.TIME_SLOTS[0]
    state["slot"] = value
    render()


def on_filter(_e, target):
    chosen = target.getAttribute("data-filter") or "all"
    state["filter"] = chosen
    for tab in ui.qsa("[data-filter]"):
        if tab.getAttribute("data-filter") == chosen:
            tab.classList.add("active")
        else:
            tab.classList.remove("active")
    render()


def on_seat(_e, target):
    seat_id = target.getAttribute("data-seat") or ""
    if not seat_id:
        return
    state["selected"] = seat_id
    for el in ui.qsa(".seat"):
        if el.getAttribute("data-seat") == seat_id:
            el.classList.add("is-selected")
        else:
            el.classList.remove("is-selected")
    render_detail()


def setup():
    today = store.today_iso()
    date_el = ui.qs("#seat-date")
    if date_el is not None:
        date_el.setAttribute("min", today)
    state["date"] = today
    ui.set_value("#seat-date", today)

    slot = current_slot()
    state["slot"] = slot
    options = "".join(
        f'<option value="{s}">{store.slot_label(s)}</option>' for s in store.TIME_SLOTS
    )
    ui.set_html("#seat-slot", options)
    ui.set_value("#seat-slot", slot)

    ui.on("#seat-date", "change", on_date)
    ui.on("#seat-slot", "change", on_slot)
    ui.on("[data-filter]", "click", on_filter)
    ui.on(".seat", "click", on_seat)

    render()
    ui.window.setInterval(ui.proxy(render), 30000)


def init():
    page = ui.current_page()
    ui.boot(page)
    if page == "seats":
        setup()


init()
