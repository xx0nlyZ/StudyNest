from pyscript import document, window

try:
    from pyodide.ffi import create_proxy
except Exception:
    try:
        from _pyodide._ffi import create_proxy
    except Exception:
        create_proxy = None

import store

PAGE_GROUP = {
    "index.html": "public",
    "about.html": "public",
    "services.html": "public",
    "pricing.html": "public",
    "contact.html": "public",
    "promo.html": "public",
    "booking.html": "booking",
    "seats.html": "booking",
    "my-bookings.html": "booking",
    "login.html": "auth",
    "register.html": "auth",
    "forgot-password.html": "auth",
    "dashboard.html": "dashboard",
}

_registry = {}
_toast_count = 0
_kept_proxies = []


def proxy(callback):
    if create_proxy is None:
        return callback
    handle = create_proxy(callback)
    _kept_proxies.append(handle)
    return handle


def _norm(node):
    if node is None or type(node).__name__ == "JsNull":
        return None
    return node


def qs(selector):
    return _norm(document.querySelector(selector))


def qsa(selector):
    return document.querySelectorAll(selector)


def exists(selector):
    return qs(selector) is not None


def set_text(selector, value):
    el = qs(selector)
    if el is not None:
        el.textContent = str(value)


def set_html(selector, value):
    el = qs(selector)
    if el is not None:
        el.innerHTML = value


def get_value(selector, default=""):
    el = qs(selector)
    if el is None:
        return default
    value = el.value
    return default if value is None else str(value).strip()


def set_value(selector, value):
    el = qs(selector)
    if el is not None:
        el.value = value


def esc(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def closest(target, selector):
    if target is None or type(target).__name__ == "JsNull":
        return None
    try:
        return _norm(target.closest(selector))
    except Exception:
        return None


def on(selector, event, handler):
    key = (event, selector)
    if key in _registry:
        return

    def wrapper(e):
        target = closest(e.target, selector)
        if target is not None:
            handler(e, target)

    document.addEventListener(event, proxy(wrapper))
    _registry[key] = True


def on_key(key, handler):
    if key in _registry:
        return
    document.addEventListener("keydown", proxy(handler))
    registry_mark(key)


def registry_mark(key):
    _registry[key] = True


def url(page):
    group = PAGE_GROUP.get(page)
    if group is None:
        return page
    return "../" + group + "/" + page


def redirect(url_value):
    window.location.href = url_value


def current_page():
    body = document.body
    if body is None:
        return ""
    page = body.getAttribute("data-page")
    return page or ""


def param(name):
    search = window.location.search or ""
    for part in str(search).lstrip("?").split("&"):
        if not part:
            continue
        bits = part.split("=", 1)
        if bits[0] == name:
            raw = bits[1] if len(bits) > 1 else ""
            try:
                return str(window.decodeURIComponent(raw))
            except Exception:
                return raw
    return ""


def _encode(value):
    return str(window.encodeURIComponent(str(value)))


def download_text(filename, content):
    uri = "data:text/plain;charset=utf-8," + _encode(content)
    link = document.createElement("a")
    link.setAttribute("href", uri)
    link.setAttribute("download", filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)


def toast(message, kind="info", duration=4200):
    global _toast_count
    host = qs(".toast-host")
    if host is None:
        host = document.createElement("div")
        host.className = "toast-host"
        document.body.appendChild(host)

    node = document.createElement("div")
    node.className = f"toast {kind}"
    node.innerHTML = f"<span>{esc(message)}</span>"
    close = document.createElement("button")
    close.className = "t-close"
    close.setAttribute("type", "button")
    close.innerHTML = "&times;"
    node.appendChild(close)
    host.appendChild(node)
    _toast_count += 1
    node.setAttribute("data-toast-id", str(_toast_count))

    def dismiss(_e=None):
        try:
            node.classList.add("out")
            window.setTimeout(proxy(lambda: _remove(node)), 260)
        except Exception:
            pass

    close.addEventListener("click", proxy(dismiss))
    window.setTimeout(proxy(dismiss), duration)


def _remove(node):
    try:
        if node.parentNode is not None:
            node.parentNode.removeChild(node)
    except Exception:
        pass


def open_modal(html, title=""):
    root = qs(".modal-root")
    if root is None:
        root = document.createElement("div")
        root.className = "modal-root"
        document.body.appendChild(root)
    title_html = f"<h3>{title}</h3>" if title else ""
    root.innerHTML = (
        '<div class="modal-backdrop" data-modal-close="1"></div>'
        '<div class="modal" role="dialog" aria-modal="true">'
        '<button class="m-close" type="button" data-modal-close="1" aria-label="Close">&times;</button>'
        f"{title_html}{html}"
        "</div>"
    )
    root.classList.add("open")
    document.body.style.overflow = "hidden"


def close_modal():
    root = qs(".modal-root")
    if root is not None:
        root.classList.remove("open")
        root.innerHTML = ""
    document.body.style.overflow = ""


def confirm_dialog(title, message, confirm_label, on_confirm, danger=True):
    cls = "btn-danger" if danger else "btn-primary"
    open_modal(
        f'<div class="m-body">{message}</div>'
        f'<div class="m-actions">'
        f'<button type="button" class="btn btn-ghost btn-sm" data-modal-close="1">Keep it</button>'
        f'<button type="button" class="btn {cls} btn-sm" id="confirm-yes">{esc(confirm_label)}</button>'
        f"</div>",
        title,
    )

    def handler(_e):
        close_modal()
        on_confirm()

    button = qs("#confirm-yes")
    if button is not None:
        button.addEventListener("click", proxy(handler))


def status_text():
    try:
        d = window.Date.new()
        hour = d.getHours() + d.getMinutes() / 60.0
    except Exception:
        hour = 0
    if store.OPEN_HOUR <= hour < store.CLOSE_HOUR:
        end = int(store.CLOSE_HOUR)
        return True, f"Open now \u00b7 until {end}:00 PM"
    if hour < store.OPEN_HOUR:
        return False, f"Closed \u00b7 opens at {store.OPEN_HOUR}:00 AM"
    return False, f"Closed \u00b7 opens at {store.OPEN_HOUR}:00 AM tomorrow"


def paint_status():
    is_open, text = status_text()
    for el in qsa(".js-status"):
        el.textContent = text
        el.classList.remove("status-open", "status-closed")
        el.classList.add("status-open" if is_open else "status-closed")


def auth_slot_html():
    user = store.current_user()
    if user:
        initials = "".join([part[0] for part in user.get("name", "S").split()[:2]]).upper()
        first = user.get("name", "").split(" ")[0]
        return (
            '<div class="nav-user show">'
            f'<span class="nav-avatar">{esc(initials)}</span>'
            f'<span class="nav-user-name">{esc(first)}</span>'
            f'<a href="{url("dashboard.html")}" class="btn btn-primary btn-sm">Dashboard</a>'
            '<button type="button" class="nav-logout" id="nav-logout">Log out</button>'
            "</div>"
        )
    return (
        f'<a href="{url("login.html")}" class="btn btn-ghost btn-sm">Log in</a>'
        f'<a href="{url("register.html")}" class="btn btn-primary btn-sm">Sign up</a>'
    )


def paint_auth_slot():
    slot = qs("#nav-auth")
    if slot is not None:
        slot.innerHTML = auth_slot_html()


def paint_active_nav():
    page = current_page()
    if not page:
        return
    for link in qsa(".nav-links a[data-nav]"):
        link.classList.remove("active")
        if link.getAttribute("data-nav") == page:
            link.classList.add("active")


def mark_ready(page):
    document.documentElement.setAttribute("data-py-ready", page)


def boot(page):
    paint_status()
    paint_auth_slot()
    paint_active_nav()
    window.setInterval(proxy(paint_status), 30000)
    on("#nav-toggle", "click", _nav_toggle)
    on(".nav-links a", "click", _nav_link)
    on("#nav-logout", "click", _logout)
    on("[data-modal-close]", "click", lambda e, t: close_modal())
    on_key("modal-esc", _escape)
    _track_scroll()
    mark_ready(page)


def _nav_toggle(e, target):
    links = qs("#nav-links")
    if links is None:
        return
    is_open = links.classList.toggle("open")
    target.classList.toggle("active", bool(is_open))
    target.setAttribute("aria-expanded", "true" if is_open else "false")


def _nav_link(e, target):
    links = qs("#nav-links")
    toggle = qs("#nav-toggle")
    if links is not None:
        links.classList.remove("open")
    if toggle is not None:
        toggle.classList.remove("active")
        toggle.setAttribute("aria-expanded", "false")
    paint_active_nav()


def _logout(e, target):
    store.logout()
    paint_auth_slot()
    toast("You have been logged out.", "ok")
    window.setTimeout(proxy(_go_home), 500)


def _go_home():
    redirect(url("index.html"))


def _escape(e):
    try:
        if e.key == "Escape":
            close_modal()
    except Exception:
        pass


def _track_scroll():
    def handler(_e=None):
        nav = qs(".nav")
        if nav is not None:
            nav.classList.toggle("scrolled", (window.scrollY or 0) > 8)

    window.addEventListener("scroll", proxy(handler))
    handler()
