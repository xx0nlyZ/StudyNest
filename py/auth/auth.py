import re
import store
import ui

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def init():
    page = ui.current_page()
    ui.boot(page)

    user = store.current_user()
    if user and (page == "login" or page == "register"):
        ui.toast("Already signed in. Redirecting...", "ok")
        ui.redirect(ui.url("dashboard.html"))
        return

    if page == "login":
        setup_login()
        setup_forgot()
    elif page == "register":
        setup_register()

def set_invalid(input_el, err_el, msg):
    if input_el is not None:
        input_el.classList.add("invalid")
    if err_el is not None:
        err_el.textContent = msg or ""

def clear_invalid(input_el, err_el):
    if input_el is not None:
        input_el.classList.remove("invalid")
    if err_el is not None:
        err_el.textContent = ""

def err_for(form, name):
    el = ui.qs(form + " [data-err='" + name + "']")
    return el

def input_for(form, selector):
    return ui.qs(form + " " + selector)

def show_alert(msg):
    al = ui.qs("#auth-alert")
    if al is not None:
        if msg:
            al.textContent = msg
            al.classList.remove("hidden")
        else:
            al.textContent = ""
            al.classList.add("hidden")

def toggle_pw(target):
    inp = ui.closest(target, ".input-group")
    if inp is None:
        return
    input_el = inp.querySelector(".input")
    if input_el is None:
        return
    if input_el.type == "password":
        input_el.type = "text"
        target.textContent = "Hide"
    else:
        input_el.type = "password"
        target.textContent = "Show"

def strength_score(pw):
    s = 0
    if len(pw) >= 8:
        s += 1
    if re.search(r"[A-Za-z]", pw) and re.search(r"\d", pw):
        s += 1
    if re.search(r"[^A-Za-z0-9]", pw):
        s += 1
    if len(pw) >= 12:
        s += 1
    return min(s, 4)

def update_strength(pw):
    bar = ui.qs("#pw-strength")
    if bar is None:
        return
    sc = strength_score(pw or "")
    bar.className = "strength s" + str(sc)

def digits_only(v):
    return re.sub(r"\D", "", v or "")

def setup_login():
    form = "#login-form"
    if ui.qs(form) is None:
        return
    ui.on(form, "submit", on_login_submit)
    ui.on("[data-action='toggle-password']", "click", lambda e, t: toggle_pw(t))
    ui.on("[data-action='fill-demo']", "click", lambda e, t: fill_demo())

def fill_demo():
    ui.set_value("#login-email", "maria@studynest.ph")
    ui.set_value("#login-password", "studynest123")
    p = ui.qs("#login-password")
    if p is not None:
        p.type = "password"
    btn = ui.qs("[data-action='toggle-password']")
    if btn is not None:
        btn.textContent = "Show"

def on_login_submit(e, t):
    e.preventDefault()
    show_alert("")
    email = ui.get_value("#login-email")
    pw = ui.get_value("#login-password")
    ok = True
    clear_invalid(ui.qs("#login-email"), err_for("#login-form", "email"))
    clear_invalid(ui.qs("#login-password"), err_for("#login-form", "password"))
    if not EMAIL_RE.match(email):
        set_invalid(ui.qs("#login-email"), err_for("#login-form", "email"), "Enter a valid email address.")
        ok = False
    if len(pw) < 6:
        set_invalid(ui.qs("#login-password"), err_for("#login-form", "password"), "Password must be at least 6 characters.")
        ok = False
    if not ok:
        ui.toast("Please fix the login details.", "err")
        return
    res = store.login(email, pw)
    if res[0]:
        ui.toast(res[1] or "Welcome back.", "ok")
        ui.redirect(ui.url("dashboard.html"))
    else:
        msg = res[1] or "Login failed."
        show_alert(msg)
        ui.toast("Login failed.", "err")

def setup_register():
    form = "#register-form"
    if ui.qs(form) is None:
        return
    ui.on(form, "submit", on_register_submit)
    ui.on("[data-action='toggle-password']", "click", lambda e, t: toggle_pw(t))
    pw = ui.qs("#reg-password")
    if pw is not None:
        pw.addEventListener("input", ui.proxy(lambda e: update_strength(ui.get_value("#reg-password"))))

def on_register_submit(e, t):
    e.preventDefault()
    show_alert("")
    name = ui.get_value("#reg-name")
    email = ui.get_value("#reg-email")
    phone = ui.get_value("#reg-phone")
    student_id = ui.get_value("#reg-studentid")
    pw = ui.get_value("#reg-password")
    confirm = ui.get_value("#reg-confirm")
    terms = ui.qs("#reg-terms")
    agreed = terms is not None and terms.checked

    ok = True
    clear_invalid(ui.qs("#reg-name"), err_for("#register-form", "name"))
    clear_invalid(ui.qs("#reg-email"), err_for("#register-form", "email"))
    clear_invalid(ui.qs("#reg-phone"), err_for("#register-form", "phone"))
    clear_invalid(ui.qs("#reg-studentid"), err_for("#register-form", "student_id"))
    clear_invalid(ui.qs("#reg-password"), err_for("#register-form", "password"))
    clear_invalid(ui.qs("#reg-confirm"), err_for("#register-form", "confirm"))
    err_t = err_for("#register-form", "terms")
    if err_t is not None:
        err_t.textContent = ""

    if len(name.strip()) < 2:
        set_invalid(ui.qs("#reg-name"), err_for("#register-form", "name"), "Enter your full name.")
        ok = False
    if not EMAIL_RE.match(email):
        set_invalid(ui.qs("#reg-email"), err_for("#register-form", "email"), "Enter a valid email address.")
        ok = False
    if len(digits_only(phone)) < 10:
        set_invalid(ui.qs("#reg-phone"), err_for("#register-form", "phone"), "Enter a valid mobile number.")
        ok = False
    if len(pw) < 8:
        set_invalid(ui.qs("#reg-password"), err_for("#register-form", "password"), "Password must be at least 8 characters.")
        ok = False
    if pw != confirm:
        set_invalid(ui.qs("#reg-confirm"), err_for("#register-form", "confirm"), "Passwords do not match.")
        ok = False
    if not agreed:
        err_t = err_for("#register-form", "terms")
        if err_t is not None:
            err_t.textContent = "You must agree to the terms."
        ok = False

    if not ok:
        ui.toast("Please fix the registration details.", "err")
        return
    res = store.register(name, email, phone, student_id, pw)
    if res[0]:
        first = name.strip().split(" ")[0]
        ui.toast("Welcome to StudyNest, " + first + "!", "ok")
        ui.redirect(ui.url("dashboard.html"))
    else:
        msg = res[1] or "Registration failed."
        show_alert(msg)
        ui.toast("Registration failed.", "err")

def setup_forgot():
    form = "#forgot-form"
    if ui.qs(form) is None:
        return
    ui.on(form, "submit", on_forgot_submit)
    ui.on("[data-action='toggle-password']", "click", lambda e, t: toggle_pw(t))

def on_forgot_submit(e, t):
    e.preventDefault()
    show_alert("")
    email = ui.get_value("#fp-email")
    pw = ui.get_value("#fp-password")
    confirm = ui.get_value("#fp-confirm")
    ok = True
    clear_invalid(ui.qs("#fp-email"), err_for("#forgot-form", "email"))
    clear_invalid(ui.qs("#fp-password"), err_for("#forgot-form", "password"))
    clear_invalid(ui.qs("#fp-confirm"), err_for("#forgot-form", "confirm"))
    if not EMAIL_RE.match(email):
        set_invalid(ui.qs("#fp-email"), err_for("#forgot-form", "email"), "Enter a valid email address.")
        ok = False
    if len(pw) < 6:
        set_invalid(ui.qs("#fp-password"), err_for("#forgot-form", "password"), "Password must be at least 6 characters.")
        ok = False
    if pw != confirm:
        set_invalid(ui.qs("#fp-confirm"), err_for("#forgot-form", "confirm"), "Passwords do not match.")
        ok = False
    if not ok:
        ui.toast("Please fix the form details.", "err")
        return
    res = store.reset_password(email, pw)
    if res[0]:
        ui.toast(res[1] or "Password updated.", "ok")
        ui.redirect(ui.url("login.html"))
    else:
        msg = res[1] or "Reset failed."
        show_alert(msg)
        ui.toast("Reset failed.", "err")

init()