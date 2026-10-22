import ui

SIDES = ("left", "right")

state = {
    "active": "left",
    "url": {"left": "", "right": ""},
    "name": {"left": "", "right": ""},
    "dragging": {"left": False, "right": False},
}


def el(side, suffix):
    return ui.qs(f"#{side}-{suffix}")


def video(side):
    return el(side, "video")


def side_of(target):
    if target is None:
        return ""
    try:
        value = target.getAttribute("data-side") or ""
    except Exception:
        value = ""
    return value if value in SIDES else ""


def fmt_time(seconds):
    try:
        total = int(float(seconds))
    except Exception:
        total = 0
    if total < 0:
        total = 0
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def has_source(side):
    return bool(state["url"][side])


def duration_of(side):
    v = video(side)
    if v is None:
        return 0.0
    try:
        value = float(v.duration)
    except Exception:
        return 0.0
    if value != value or value < 0:
        return 0.0
    return value


def current_of(side):
    v = video(side)
    if v is None:
        return 0.0
    try:
        return float(v.currentTime)
    except Exception:
        return 0.0


def is_playing(side):
    v = video(side)
    if v is None:
        return False
    try:
        return not bool(v.paused)
    except Exception:
        return False


def is_muted(side):
    v = video(side)
    if v is None:
        return False
    try:
        return bool(v.muted)
    except Exception:
        return False


def paint_pane(side):
    stage = el(side, "stage")
    empty = el(side, "empty")
    name_el = el(side, "name")
    seek = el(side, "seek")
    play = el(side, "play")
    mute = el(side, "mute")
    full = el(side, "full")

    loaded = has_source(side)

    if stage is not None:
        stage.classList.toggle("has-video", loaded)
    if empty is not None:
        empty.classList.toggle("hidden", loaded)
    if name_el is not None:
        name_el.textContent = state["name"][side] or "No source"
        name_el.classList.toggle("is-empty", not loaded)
    if seek is not None:
        seek.disabled = not loaded
    if play is not None:
        playing = is_playing(side)
        play.textContent = "\u275a\u275a" if playing else "\u25b6"
        play.title = "Pause" if playing else "Play"
        play.setAttribute("aria-label", f"{play.title} {side} video")
        play.disabled = not loaded
    if mute is not None:
        muted = is_muted(side)
        mute.textContent = "\U0001f507" if muted else "\U0001f50a"
        mute.classList.toggle("is-on", muted)
    if full is not None:
        full.disabled = not loaded


def paint_time(side):
    time_el = el(side, "time")
    seek = el(side, "seek")
    duration = duration_of(side)
    current = current_of(side)
    if time_el is not None:
        time_el.textContent = f"{fmt_time(current)} / {fmt_time(duration)}"
    if seek is not None and not state["dragging"][side]:
        try:
            seek.value = str(int((current / duration) * 1000)) if duration > 0 else "0"
        except Exception:
            pass


def paint_all():
    for side in SIDES:
        paint_pane(side)
        paint_time(side)


def set_source(side, src, name=""):
    v = video(side)
    if v is None or not src:
        return
    state["url"][side] = src
    state["name"][side] = name or src.split("/")[-1].split("?")[0] or "Source"
    try:
        if (v.getAttribute("src") or "") != src:
            v.setAttribute("src", src)
            v.load()
    except Exception:
        pass
    paint_all()


def clear_source(side):
    v = video(side)
    if v is not None:
        try:
            v.pause()
            v.removeAttribute("src")
            v.load()
        except Exception:
            pass
    state["url"][side] = ""
    state["name"][side] = ""
    state["dragging"][side] = False
    paint_all()


def safe_play(v):
    try:
        result = v.play()
        if result is not None:
            try:
                result.catch(ui.proxy(lambda _err: None))
            except Exception:
                pass
    except Exception:
        pass


def play(side):
    v = video(side)
    if v is None or not has_source(side):
        return
    state["active"] = side
    safe_play(v)
    paint_all()


def pause(side):
    v = video(side)
    if v is None:
        return
    try:
        v.pause()
    except Exception:
        pass
    paint_all()


def toggle_play(side):
    if is_playing(side):
        pause(side)
    else:
        play(side)


def toggle_all():
    playing = any(is_playing(side) for side in SIDES)
    for side in SIDES:
        if playing:
            pause(side)
        else:
            play(side)


def seek_by(side, seconds):
    v = video(side)
    if v is None or not has_source(side):
        return
    duration = duration_of(side)
    if duration <= 0:
        return
    target = current_of(side) + seconds
    target = max(0.0, min(duration, target))
    try:
        v.currentTime = target
    except Exception:
        pass
    paint_time(side)


def on_timeupdate(side):
    paint_time(side)


def on_metadata(side):
    paint_pane(side)
    paint_time(side)


def on_ended(side):
    paint_all()


def on_play_event(side):
    paint_pane(side)


def on_pause_event(side):
    paint_pane(side)


def on_volume_event(side):
    paint_pane(side)


def bind_media(side):
    v = video(side)
    if v is None:
        return
    pairs = (
        ("timeupdate", lambda _e: on_timeupdate(side)),
        ("loadedmetadata", lambda _e: on_metadata(side)),
        ("ended", lambda _e: on_ended(side)),
        ("play", lambda _e: on_play_event(side)),
        ("pause", lambda _e: on_pause_event(side)),
        ("volumechange", lambda _e: on_volume_event(side)),
    )
    for event, handler in pairs:
        try:
            v.addEventListener(event, ui.proxy(handler))
        except Exception:
            pass


def on_play_click(_e, target):
    side = side_of(target)
    if side:
        toggle_play(side)


def on_mute_click(_e, target):
    side = side_of(target)
    v = video(side)
    if v is None:
        return
    try:
        v.muted = not bool(v.muted)
    except Exception:
        pass
    paint_pane(side)


def on_full_click(_e, target):
    v = video(side_of(target))
    if v is None:
        return
    try:
        result = v.requestFullscreen()
        if result is not None:
            try:
                result.catch(ui.proxy(lambda _err: None))
            except Exception:
                pass
    except Exception:
        pass


def on_video_click(_e, target):
    side = side_of(target)
    if side:
        toggle_play(side)


def on_seek(_e, target):
    side = side_of(target)
    v = video(side)
    if v is None or not has_source(side):
        return
    duration = duration_of(side)
    if duration <= 0:
        return
    try:
        ratio = float(target.value) / 1000.0
    except Exception:
        ratio = 0.0
    ratio = max(0.0, min(1.0, ratio))
    try:
        v.currentTime = duration * ratio
    except Exception:
        pass
    state["dragging"][side] = True
    state["active"] = side
    paint_time(side)


def on_seek_end(_e, target):
    side = side_of(target)
    if side:
        state["dragging"][side] = False


def on_volume(_e, target):
    side = side_of(target)
    v = video(side)
    if v is None:
        return
    try:
        value = float(target.value)
    except Exception:
        value = 100.0
    try:
        v.volume = max(0.0, min(1.0, value / 100.0))
    except Exception:
        pass


def on_key(e):
    try:
        key = e.key
    except Exception:
        return
    try:
        tag = e.target.tagName
    except Exception:
        tag = ""
    if tag in ("INPUT", "TEXTAREA", "SELECT"):
        return
    key = str(key)
    if key == " " or key == "Spacebar":
        try:
            e.preventDefault()
        except Exception:
            pass
        toggle_all()
    elif key == "ArrowLeft":
        try:
            e.preventDefault()
        except Exception:
            pass
        seek_by(state["active"], -5)
    elif key == "ArrowRight":
        try:
            e.preventDefault()
        except Exception:
            pass
        seek_by(state["active"], 5)


def initial_source(side):
    v = video(side)
    if v is None:
        return ""
    try:
        return v.getAttribute("src") or ""
    except Exception:
        return ""


def apply_params():
    for side in SIDES:
        src = ui.param(side) or initial_source(side)
        if src:
            set_source(side, src)


def setup():
    ui.on(".player-play", "click", on_play_click)
    ui.on(".player-mute", "click", on_mute_click)
    ui.on(".player-full", "click", on_full_click)
    ui.on(".player-seek", "input", on_seek)
    ui.on(".player-seek", "change", on_seek_end)
    ui.on(".player-volume", "input", on_volume)
    ui.on(".video-stage video", "click", on_video_click)
    ui.on_key("split-keys", on_key)

    for side in SIDES:
        bind_media(side)

    paint_all()
    apply_params()


def init():
    page = ui.current_page()
    ui.boot(page)
    if page == "split":
        setup()


init()
