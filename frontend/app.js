/* SANEK portfolio app */
"use strict";

const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

const I18N = {
  ru: {
    "nav.works": "Работы", "nav.services": "Услуги", "nav.exhibitions": "Выставки", "nav.contacts": "Контакты", "nav.book": "Записаться",
    "hero.overline": "Портфолио — editorial & fine art",
    "hero.book": "Записаться на съёмку", "hero.works": "Смотреть работы", "hero.scroll": "листайте вниз",
    "about.label": "Обо мне",
    "stats.years": "лет опыта", "stats.shoots": "съёмок", "stats.countries": "стран",
    "works.label": "Работы", "works.title": "Избранные серии", "works.empty": "Работы скоро появятся.",
    "pills.all": "Все",
    "selected.label": "Selected works",
    "services.label": "Услуги", "services.title": "Форматы съёмки", "services.empty": "Услуги скоро появятся.", "services.choose": "Выбрать",
    "ex.label": "Выставки и награды", "ex.empty": "Список скоро появится.",
    "contacts.label": "Контакты", "contacts.title": "Давайте создадим что-то выдающееся",
    "contacts.note": "Отвечаю в течение дня. Для коммерческих запросов — пожалуйста, сразу опишите задачу.",
    "c.phone": "Телефон", "c.telegram": "Telegram", "c.whatsapp": "WhatsApp", "c.instagram": "Instagram", "c.behance": "Behance", "c.email": "Почта",
    "booking.label": "Запись", "booking.title": "Записаться на съёмку",
    "booking.sub": "Оставьте заявку — я свяжусь с вами, чтобы обсудить детали.",
    "booking.name": "Ваше имя", "booking.name_ph": "Как к вам обращаться",
    "booking.contact": "Телефон или Telegram", "booking.contact_ph": "+7 ___ ___-__-__ или @username",
    "booking.service": "Услуга", "booking.any": "Пока не определился",
    "booking.date": "Желаемая дата", "booking.date_ph": "Например: середина октября",
    "booking.message": "О съёмке", "booking.message_ph": "Пара слов о задаче, городе, настроении",
    "booking.submit": "Отправить заявку", "booking.sending": "Отправка...",
    "booking.note": "Нажимая кнопку, вы соглашаетесь на обработку персональных данных.",
    "booking.success_title": "Заявка отправлена", "booking.success_text": "Спасибо! Я свяжусь с вами в ближайшее время.",
    "booking.more": "Отправить ещё одну",
    "booking.error": "Не получилось отправить. Проверьте поля и попробуйте ещё раз.",
    "booking.fill": "Заполните имя и контакт для связи.",
    "album.back": "Все работы",
    "album.photos": ["фотография", "фотографии", "фотографий"],
  },
  en: {
    "nav.works": "Works", "nav.services": "Services", "nav.exhibitions": "Exhibitions", "nav.contacts": "Contact", "nav.book": "Book",
    "hero.overline": "Portfolio — editorial & fine art",
    "hero.book": "Book a shoot", "hero.works": "View works", "hero.scroll": "scroll down",
    "about.label": "About",
    "stats.years": "years of experience", "stats.shoots": "shoots", "stats.countries": "countries",
    "works.label": "Works", "works.title": "Selected series", "works.empty": "Works coming soon.",
    "pills.all": "All",
    "selected.label": "Selected works",
    "services.label": "Services", "services.title": "Shoot formats", "services.empty": "Services coming soon.", "services.choose": "Choose",
    "ex.label": "Exhibitions & awards", "ex.empty": "List coming soon.",
    "contacts.label": "Contact", "contacts.title": "Let's create something outstanding",
    "contacts.note": "I reply within a day. For commercial inquiries — please describe the project right away.",
    "c.phone": "Phone", "c.telegram": "Telegram", "c.whatsapp": "WhatsApp", "c.instagram": "Instagram", "c.behance": "Behance", "c.email": "Email",
    "booking.label": "Booking", "booking.title": "Book a shoot",
    "booking.sub": "Leave a request — I'll get in touch to discuss the details.",
    "booking.name": "Your name", "booking.name_ph": "What should I call you",
    "booking.contact": "Phone or Telegram", "booking.contact_ph": "+7 ___ ___-__-__ or @username",
    "booking.service": "Service", "booking.any": "Not sure yet",
    "booking.date": "Preferred date", "booking.date_ph": "E.g. mid-October",
    "booking.message": "About the shoot", "booking.message_ph": "A few words on the project, city, mood",
    "booking.submit": "Send request", "booking.sending": "Sending...",
    "booking.note": "By clicking the button you agree to the processing of personal data.",
    "booking.success_title": "Request sent", "booking.success_text": "Thank you! I'll get in touch shortly.",
    "booking.more": "Send another one",
    "booking.error": "Couldn't send. Check the fields and try again.",
    "booking.fill": "Please fill in your name and contact.",
    "album.back": "All works",
    "album.photos": ["photo", "photos", "photos"],
  }
};

let LANG = "ru";
try {
  const stored = window.localStorage && window.localStorage.getItem("sanek_lang");
  if (stored) LANG = stored;
} catch (e) {}
if (!I18N[LANG]) LANG = "ru";
const t = (key) => (I18N[LANG] && I18N[LANG][key]) || I18N.ru[key] || key;

function plural(n, forms) {
  if (LANG === "ru") {
    const n10 = n % 10, n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return forms[0];
    if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return forms[1];
    return forms[2];
  }
  return n === 1 ? forms[0] : forms[1];
}

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function paragraphs(text) {
  return String(text || "")
    .split(/\n{2,}|\n/)
    .map((s) => s.trim()).filter(Boolean)
    .map((s) => `<p>${esc(s)}</p>`).join("");
}

/* Описание услуги: обычные строки — абзацы, строки с •/-/✓ — список */
function richDesc(text) {
  const lines = String(text || "").split("\n").map((s) => s.trim()).filter(Boolean);
  const paras = [], items = [];
  for (const ln of lines) {
    const m = ln.match(/^[•\-\–\—*✓]\s*(.+)/);
    if (m) items.push(m[1]); else paras.push(ln);
  }
  let html = paras.map((p) => `<p>${esc(p)}</p>`).join("");
  if (items.length) html += `<ul>${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>`;
  return html;
}

function toast(msg) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.hidden = true; }, 3200);
}

function haptic(kind) {
  try { if (tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred(kind || "success"); } catch (e) {}
}

/* ---------------- reveal on scroll ---------------- */
let revealObserver = null;
try {
  revealObserver = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) { e.target.classList.add("visible"); try { revealObserver.unobserve(e.target); } catch (err) {} }
    }
  }, { threshold: 0.08 });
} catch (e) {
  revealObserver = null;
}
function observeReveals(root) {
  const nodes = (root || document).querySelectorAll(".reveal:not(.visible)");
  if (!revealObserver) {
    nodes.forEach((el) => el.classList.add("visible"));
    return;
  }
  nodes.forEach((el) => { try { revealObserver.observe(el); } catch (err) {} });
}

/* ---------------- state ---------------- */
let SITE = null;
let activeCat = 0; // 0 = all

async function loadSite() {
  const res = await fetch("/api/site");
  if (!res.ok) throw new Error("api");
  SITE = await res.json();
}

/* ---------------- render ---------------- */
function renderAll() {
  if (!SITE) return;
  const s = SITE.settings;
  document.title = `${s.brand_name || "Photographer"} — Photographer`;
  document.getElementById("brandName").textContent = s.brand_name || "";
  document.getElementById("footerBrand").textContent = `© ${new Date().getFullYear()} ${s.brand_name || ""}`;
  document.getElementById("footerTag").textContent = s.tagline || "";

  // hero
  document.getElementById("heroName").textContent = s.brand_name || "";
  document.getElementById("heroTagline").textContent = s.tagline || "";
  const meta = [];
  if (s.city) meta.push(`<span>📍 ${esc(s.city)}</span>`);
  if (s.experience_years) meta.push(`<span><b>${esc(s.experience_years)}</b> ${esc(t("stats.years"))}</span>`);
  if (s.shoots_count) meta.push(`<span><b>${esc(s.shoots_count)}</b> ${esc(t("stats.shoots"))}</span>`);
  document.getElementById("heroMeta").innerHTML = meta.join("");
  const heroImg = document.getElementById("heroImg");
  if (s.hero_url) { heroImg.src = s.hero_url; heroImg.hidden = false; }
  else heroImg.removeAttribute("src");
  document.getElementById("heroCap").textContent = s.city || "";

  // about
  document.getElementById("aboutTitle").textContent = s.tagline || "";
  document.getElementById("aboutText").innerHTML = paragraphs(s.about);
  const avatar = document.getElementById("avatarImg");
  if (s.avatar_url) avatar.src = s.avatar_url; else avatar.removeAttribute("src");
  const facts = String(s.facts || "").split("\n").map((x) => x.trim()).filter(Boolean);
  document.getElementById("factsList").innerHTML = facts.map((f) => `<li>${esc(f.replace(/^[•\-–\—*✓]\s*/, ""))}</li>`).join("");
  const stats = [];
  if (s.experience_years) stats.push(`<div class="stat"><b>${esc(s.experience_years)}</b><span>${esc(t("stats.years"))}</span></div>`);
  if (s.shoots_count) stats.push(`<div class="stat"><b>${esc(s.shoots_count)}</b><span>${esc(t("stats.shoots"))}</span></div>`);
  if (s.countries_count) stats.push(`<div class="stat"><b>${esc(s.countries_count)}</b><span>${esc(t("stats.countries"))}</span></div>`);
  document.getElementById("statsRow").innerHTML = stats.join("");

  // marquee
  const items = [s.brand_name, ...(SITE.exhibitions || []).map((e) => e.title)].filter(Boolean);
  const half = items.map((x) => `<span><i>✦</i>${esc(x)}</span>`).join("");
  document.getElementById("marqueeTrack").innerHTML = half + half;

  renderPills();
  renderAlbums();
  renderSelected();
  renderServices();
  renderExhibitions();
  renderContacts();
  renderServiceOptions();
  renderBookingVisibility();
  observeReveals();
}

function renderPills() {
  const pills = document.getElementById("catPills");
  let html = `<button class="pill${activeCat === 0 ? " active" : ""}" data-cat="0">${esc(t("pills.all"))}</button>`;
  for (const c of SITE.categories) {
    const n = c.albums.length;
    html += `<button class="pill${activeCat === c.id ? " active" : ""}" data-cat="${c.id}">${esc(c.title)}<small>${n}</small></button>`;
  }
  pills.innerHTML = html;
  pills.querySelectorAll(".pill").forEach((b) => b.addEventListener("click", () => {
    activeCat = Number(b.dataset.cat);
    renderPills(); renderAlbums(); observeReveals();
  }));
}

function albumCard(a, catTitle) {
  const cover = a.cover ? (a.cover.thumb || a.cover.url) : "";
  const meta = [catTitle, a.location, a.year].filter(Boolean).map(esc).join(" · ");
  return `
  <a class="album-card reveal" data-album="${a.id}">
    <div class="album-cover">${cover ? `<img src="${esc(cover)}" alt="${esc(a.title)}" loading="lazy">` : ""}
      <span class="album-count">${a.count} ${esc(plural(a.count, t("album.photos")))}</span></div>
    <div class="album-info"><h3>${esc(a.title)} <span class="arr">→</span></h3>
    ${meta ? `<div class="album-meta">${meta}</div>` : ""}</div>
  </a>`;
}

function renderAlbums() {
  const grid = document.getElementById("albumsGrid");
  const cats = SITE.categories.filter((c) => !activeCat || c.id === activeCat);
  let html = "";
  for (const c of cats) for (const a of c.albums) html += albumCard(a, c.title);
  grid.innerHTML = html;
  document.getElementById("worksEmpty").hidden = html !== "";
  grid.querySelectorAll("[data-album]").forEach((el) =>
    el.addEventListener("click", () => openAlbum(Number(el.dataset.album))));
}

function renderSelected() {
  const sec = document.getElementById("selected");
  const row = document.getElementById("selectedRow");
  const items = SITE.selected || [];
  if (!items.length) { sec.hidden = true; return; }
  sec.hidden = false;
  row.innerHTML = items.map((p, i) =>
    `<img src="${esc(p.thumb || p.url)}" alt="${esc(p.caption || "Selected work")}" loading="lazy" data-sel="${i}">`).join("");
  row.querySelectorAll("[data-sel]").forEach((img) =>
    img.addEventListener("click", () => openLightbox(items, Number(img.dataset.sel))));
}

function renderServices() {
  const grid = document.getElementById("servicesGrid");
  const list = SITE.services || [];
  document.getElementById("servicesEmpty").hidden = list.length > 0;
  grid.innerHTML = list.map((s, i) => `
    <article class="service-card reveal">
      ${s.cover ? `<img class="service-cover" src="${esc(s.cover_thumb || s.cover)}" alt="${esc(s.title)}" loading="lazy">` : ""}
      <div class="service-body">
        <span class="service-idx">0${i + 1}</span>
        <h3>${esc(s.title)}</h3>
        ${s.price ? `<div class="service-price">${esc(s.price)}${s.price_note ? `<small>${esc(s.price_note)}</small>` : ""}</div>` : ""}
        ${s.duration ? `<span class="service-duration">⏱ ${esc(s.duration)}</span>` : ""}
        ${s.description ? `<div class="service-desc">${richDesc(s.description)}</div>` : ""}
        ${(s.photos && s.photos.length) ? `<div class="service-thumbs">${s.photos.slice(0, 4).map((p, pi) =>
          `<img src="${esc(p.thumb || p.url)}" alt="" loading="lazy" data-svc="${s.id}" data-pi="${pi}">`).join("")}</div>` : ""}
        <button class="btn btn-dark" data-book="${s.id}">＋ ${esc(t("services.choose"))}</button>
      </div>
    </article>`).join("");
  grid.querySelectorAll("[data-svc]").forEach((img) => {
    const svc = list.find((x) => x.id === Number(img.dataset.svc));
    img.addEventListener("click", () => openLightbox(svc.photos, Number(img.dataset.pi)));
  });
  grid.querySelectorAll("[data-book]").forEach((b) => b.addEventListener("click", () => {
    const sel = document.getElementById("fService");
    if (sel) sel.value = String(b.dataset.book);
    const dest = document.getElementById("booking");
    if (dest) {
      try {
        if (dest.scrollIntoView) dest.scrollIntoView({ behavior: "smooth" });
        else location.hash = "#booking";
      } catch (e) { location.hash = "#booking"; }
    }
    haptic("success");
  }));
}

function renderExhibitions() {
  const list = SITE.exhibitions || [];
  document.getElementById("exEmpty").hidden = list.length > 0;
  document.getElementById("exList").innerHTML = list.map((e) => `
    <div class="ex-row reveal">
      <span class="ex-year">${esc(e.year || "")}</span>
      <h3>${esc(e.title)}</h3>
      <span class="ex-place">${esc(e.place || "")}</span>
      ${e.description ? `<div class="ex-desc">${esc(e.description)}</div>` : ""}
    </div>`).join("");
}

function shortUrl(url) {
  return String(url || "").replace(/^https?:\/\//, "").replace(/\/$/, "");
}

function renderContacts() {
  const s = SITE.settings;
  const rows = [];
  if (s.phone) rows.push({ label: t("c.phone"), value: s.phone, href: `tel:${s.phone.replace(/[^+\d]/g, "")}` });
  if (s.telegram) rows.push({ label: t("c.telegram"), value: shortUrl(s.telegram), href: s.telegram });
  const wa = String(s.whatsapp || "").replace(/\D/g, "");
  if (wa) rows.push({ label: t("c.whatsapp"), value: "+" + wa, href: `https://wa.me/${wa}` });
  if (s.instagram) rows.push({ label: t("c.instagram"), value: shortUrl(s.instagram), href: s.instagram });
  if (s.behance) rows.push({ label: t("c.behance"), value: shortUrl(s.behance), href: s.behance });
  if (s.email) rows.push({ label: t("c.email"), value: s.email, href: `mailto:${s.email}` });
  document.getElementById("contactLinks").innerHTML = rows.map((r) => `
    <a class="contact-row reveal" href="${esc(r.href)}" target="_blank" rel="noopener">
      <span class="c-label">${esc(r.label)}</span><span class="c-value">${esc(r.value)}</span><span class="c-arr">↗</span>
    </a>`).join("");
}

function renderServiceOptions() {
  const sel = document.getElementById("fService");
  const cur = sel.value;
  sel.innerHTML = `<option value="">${esc(t("booking.any"))}</option>` +
    (SITE.services || []).map((s) => `<option value="${s.id}">${esc(s.title)}${s.price ? ` — ${esc(s.price)}` : ""}</option>`).join("");
  sel.value = cur;
}

function renderBookingVisibility() {
  const on = (SITE.settings.booking_enabled || "1") === "1";
  document.getElementById("booking").style.display = on ? "" : "none";
}

/* ---------------- album overlay ---------------- */
let albumPhotos = [];

async function openAlbum(id) {
  try {
    const res = await fetch(`/api/album/${id}`);
    if (!res.ok) throw 0;
    const a = await res.json();
    albumPhotos = a.photos || [];
    const meta = [a.category, a.location, a.year].filter(Boolean).map(esc).join(" · ");
    document.getElementById("albumHead").innerHTML = `
      <div class="album-head">
        <h2>${esc(a.title)}</h2>
        <div class="a-meta">${meta}${meta ? " · " : ""}${albumPhotos.length} ${esc(plural(albumPhotos.length, t("album.photos")))}</div>
        ${a.description ? `<div class="a-desc">${esc(a.description)}</div>` : ""}
      </div>`;
    document.getElementById("albumGrid").innerHTML = albumPhotos.map((p, i) => `
      <figure data-ph="${i}"><img src="${esc(p.thumb || p.url)}" alt="${esc(p.caption || a.title)}" loading="lazy">
      ${p.caption ? `<figcaption>${esc(p.caption)}</figcaption>` : ""}</figure>`).join("");
    document.getElementById("albumGrid").querySelectorAll("[data-ph]").forEach((f) =>
      f.addEventListener("click", () => openLightbox(albumPhotos, Number(f.dataset.ph))));
    document.getElementById("albumView").hidden = false;
    document.getElementById("albumView").scrollTop = 0;
    document.body.style.overflow = "hidden";
    history.replaceState(null, "", `#album-${id}`);
    if (tg && tg.BackButton) { tg.BackButton.show(); tg.BackButton.onClick(closeAlbum); }
  } catch (e) { toast("..."); }
}

function closeAlbum() {
  document.getElementById("albumView").hidden = true;
  document.body.style.overflow = "";
  history.replaceState(null, "", location.pathname);
  if (tg && tg.BackButton) { tg.BackButton.hide(); try { tg.BackButton.offClick(closeAlbum); } catch (e) {} }
}

/* ---------------- lightbox ---------------- */
let lbPhotos = [], lbIndex = 0, lbTouchX = null;

function openLightbox(photos, index) {
  lbPhotos = photos || [];
  if (!lbPhotos.length) return;
  lbIndex = Math.max(0, Math.min(index || 0, lbPhotos.length - 1));
  document.getElementById("lightbox").hidden = false;
  document.body.style.overflow = "hidden";
  renderLb();
  document.addEventListener("keydown", lbKeys);
}

function renderLb() {
  const p = lbPhotos[lbIndex];
  const img = document.getElementById("lbImg");
  img.src = p.url || p.thumb;
  img.alt = p.caption || "";
  document.getElementById("lbCap").textContent = p.caption || "";
  document.getElementById("lbCount").textContent = lbPhotos.length > 1 ? `${lbIndex + 1} / ${lbPhotos.length}` : "";
}

function closeLightbox() {
  document.getElementById("lightbox").hidden = true;
  if (document.getElementById("albumView").hidden) document.body.style.overflow = "";
  document.removeEventListener("keydown", lbKeys);
}

function lbKeys(e) {
  if (e.key === "Escape") { closeLightbox(); return; }
  if (e.key === "ArrowRight") { lbIndex = (lbIndex + 1) % lbPhotos.length; renderLb(); }
  if (e.key === "ArrowLeft") { lbIndex = (lbIndex - 1 + lbPhotos.length) % lbPhotos.length; renderLb(); }
}

/* ---------------- booking ---------------- */
async function submitBooking(e) {
  e.preventDefault();
  const name = document.getElementById("fName").value.trim();
  const contact = document.getElementById("fContact").value.trim();
  if (!name || contact.length < 3) { toast(t("booking.fill")); return; }
  const btn = document.getElementById("bookSubmit");
  btn.disabled = true;
  btn.textContent = t("booking.sending");
  try {
    const sid = document.getElementById("fService").value;
    const res = await fetch("/api/booking", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name, contact,
        service_id: sid ? Number(sid) : null,
        date_text: document.getElementById("fDate").value.trim(),
        message: document.getElementById("fMsg").value.trim(),
      }),
    });
    if (!res.ok) throw 0;
    document.getElementById("bookForm").hidden = true;
    document.getElementById("bookSuccess").hidden = false;
    haptic("success");
  } catch (err) {
    toast(t("booking.error"));
    haptic("error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("booking.submit");
  }
}

/* ---------------- language ---------------- */
function applyLang() {
  try {
    document.documentElement.lang = LANG;
    const lb = document.getElementById("langBtn");
    if (lb) lb.textContent = LANG === "ru" ? "EN" : "RU";
    document.querySelectorAll("[data-i18n]").forEach((el) => { try { el.textContent = t(el.dataset.i18n); } catch (e) {} });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => { try { el.placeholder = t(el.dataset.i18nPh); } catch (e) {} });
    try { if (window.localStorage) window.localStorage.setItem("sanek_lang", LANG); } catch (e) {}
    if (SITE) renderAll();
  } catch (e) {}
}

/* ---------------- init ---------------- */
function initTelegram() {
  if (!tg) return;
  try {
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#F4F2ED");
    tg.setBackgroundColor("#F4F2ED");
  } catch (e) {}
}

function initChrome() {
  try {
    const header = document.getElementById("header");
    if (header) {
      window.addEventListener("scroll", () => header.classList.toggle("scrolled", window.scrollY > 24), { passive: true });
    }
    const burger = document.getElementById("burger");
    const menu = document.getElementById("mobileMenu");
    if (burger && menu) {
      burger.addEventListener("click", () => {
        const open = menu.hidden;
        menu.hidden = !open;
        document.body.classList.toggle("menu-open", open);
        document.body.style.overflow = open ? "hidden" : "";
      });
      menu.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {
        menu.hidden = true;
        document.body.classList.remove("menu-open");
        document.body.style.overflow = "";
      }));
    }
    const langBtn = document.getElementById("langBtn");
    if (langBtn) {
      langBtn.addEventListener("click", () => {
        LANG = LANG === "ru" ? "en" : "ru";
        applyLang();
      });
    }
    const albumBack = document.getElementById("albumBack");
    if (albumBack) albumBack.addEventListener("click", closeAlbum);
    const lbClose = document.getElementById("lbClose");
    if (lbClose) lbClose.addEventListener("click", closeLightbox);
    const lbPrev = document.getElementById("lbPrev");
    if (lbPrev) lbPrev.addEventListener("click", (e) => { e.stopPropagation(); lbIndex = (lbIndex - 1 + lbPhotos.length) % lbPhotos.length; renderLb(); });
    const lbNext = document.getElementById("lbNext");
    if (lbNext) lbNext.addEventListener("click", (e) => { e.stopPropagation(); lbIndex = (lbIndex + 1) % lbPhotos.length; renderLb(); });
    const lightbox = document.getElementById("lightbox");
    if (lightbox) {
      lightbox.addEventListener("click", (e) => { if (e.target.id === "lightbox") closeLightbox(); });
      lightbox.addEventListener("touchstart", (e) => { lbTouchX = e.changedTouches[0].clientX; }, { passive: true });
      lightbox.addEventListener("touchend", (e) => {
        if (lbTouchX === null) return;
        const dx = e.changedTouches[0].clientX - lbTouchX;
        if (Math.abs(dx) > 50) {
          lbIndex = (lbIndex + (dx < 0 ? 1 : -1) + lbPhotos.length) % lbPhotos.length;
          renderLb();
        }
        lbTouchX = null;
      }, { passive: true });
    }
    const bookForm = document.getElementById("bookForm");
    if (bookForm) bookForm.addEventListener("submit", submitBooking);
    const bookAgain = document.getElementById("bookAgain");
    if (bookAgain) bookAgain.addEventListener("click", () => {
      const bf = document.getElementById("bookForm");
      const bs = document.getElementById("bookSuccess");
      if (bf) bf.hidden = false;
      if (bs) bs.hidden = true;
    });
  } catch (e) {
    console.error("initChrome failed", e);
  }
}

async function boot() {
  try { initTelegram(); } catch (e) {}
  try { initChrome(); } catch (e) { console.error(e); }
  try { applyLang(); } catch (e) {}
  try { observeReveals(); } catch (e) {}
  try {
    await loadSite();
    renderAll();
  } catch (e) {
    toast("Ошибка загрузки. Обновите страницу.");
  }
  setTimeout(() => {
    try {
      const pr = document.getElementById("preloader");
      if (pr) pr.classList.add("hide");
    } catch (e) {}
  }, 500);
  // deep-link в альбом
  try {
    const m = location.hash.match(/^#album-(\d+)/);
    if (m && SITE) openAlbum(Number(m[1]));
  } catch (e) {}
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
