/**
 * app.js — Main application logic for index.html (mod listing page).
 */

import { fetchMods, fetchTags, fetchStats } from "./api.js";
import { formatBytes, timeAgo, copyToClipboard, debounce, ratingClass } from "./utils.js";

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  search:       "",
  activeTags:   new Set(),
  sort:         "newest",
  page:         1,
  totalPages:   Infinity,
  loading:      false,
  hasMore:      true,
};

// ── DOM refs ───────────────────────────────────────────────────────────────
const grid       = document.getElementById("mod-grid");
const searchInput = document.getElementById("search-input");
const sortItems  = document.querySelectorAll(".sort-list li");
const tagPills   = document.getElementById("tag-pills");
const statsBadge = document.getElementById("stats-badge");
const sentinel   = document.getElementById("scroll-sentinel");
const loader     = document.getElementById("loading-indicator");
const modal      = document.getElementById("modal-overlay");
const modalBody  = document.getElementById("modal-body");

// ── Bootstrap ──────────────────────────────────────────────────────────────
(async function init() {
  await Promise.all([loadTags(), loadStats()]);
  await loadMods(true);
  setupIntersectionObserver();
})();

// ── Data loaders ───────────────────────────────────────────────────────────
async function loadMods(reset = false) {
  if (state.loading || !state.hasMore) return;

  if (reset) {
    state.page    = 1;
    state.hasMore = true;
    grid.innerHTML = "";
  }

  state.loading = true;
  loader.hidden = false;

  try {
    const data = await fetchMods({
      search: state.search,
      tags:   [...state.activeTags],
      sort:   state.sort,
      page:   state.page,
      limit:  24,
    });

    renderCards(data.items);
    state.page++;
    state.hasMore = grid.children.length < data.total;
  } catch (err) {
    console.error("Failed to load mods:", err);
  } finally {
    state.loading = false;
    loader.hidden = true;
  }
}

async function loadTags() {
  try {
    const tags = await fetchTags();
    tagPills.innerHTML = tags
      .slice(0, 30)
      .map(({ tag }) => `<button class="tag-pill" data-tag="${tag}">${tag}</button>`)
      .join("");

    tagPills.addEventListener("click", e => {
      const pill = e.target.closest(".tag-pill");
      if (!pill) return;
      const tag = pill.dataset.tag;
      if (state.activeTags.has(tag)) {
        state.activeTags.delete(tag);
        pill.classList.remove("active");
      } else {
        state.activeTags.add(tag);
        pill.classList.add("active");
      }
      loadMods(true);
    });
  } catch (err) {
    console.error("Failed to load tags:", err);
  }
}

async function loadStats() {
  try {
    const s = await fetchStats();
    statsBadge.textContent = `${s.total_mods.toLocaleString()} mods · updated ${timeAgo(s.last_scraped_at)}`;
  } catch (_) {}
}

// ── Render ─────────────────────────────────────────────────────────────────
function renderCards(mods) {
  mods.forEach(mod => {
    const card = document.createElement("div");
    card.className = "mod-card";
    card.dataset.id = mod.id;

    const rc = ratingClass(mod.rating);
    const tags = (mod.tags || []).slice(0, 3)
      .map(t => `<span class="mod-card__tag">${t}</span>`)
      .join("");

    card.innerHTML = `
      <img class="mod-card__thumb"
           src="${mod.thumbnail_url || ""}"
           alt="${mod.name}"
           loading="lazy"
           onerror="this.style.display='none'">
      <div class="mod-card__body">
        <div class="mod-card__name">${mod.name}</div>
        <div class="mod-card__author">${mod.author || "Unknown"}</div>
        <div class="mod-card__tags">${tags}</div>
        <div class="mod-card__meta">
          <span>${formatBytes(mod.size_bytes)}</span>
          ${mod.rating != null ? `<span class="rating ${rc}">${Math.round(mod.rating)}%</span>` : ""}
        </div>
      </div>`;

    card.addEventListener("click", () => openModal(mod.id));
    grid.appendChild(card);
  });
}

// ── Modal ──────────────────────────────────────────────────────────────────
async function openModal(modId) {
  modal.classList.add("open");
  modalBody.innerHTML = `<div class="loading-indicator">Loading…</div>`;

  try {
    const { fetchMod } = await import("./api.js");
    const mod = await fetchMod(modId);
    renderModal(mod);
  } catch (err) {
    modalBody.innerHTML = `<div class="loading-indicator">Failed to load mod details.</div>`;
  }
}

function renderModal(mod) {
  const rc = ratingClass(mod.rating);
  const gallery = (mod.image_urls || [])
    .map(u => `<img src="${u}" alt="" loading="lazy">`)
    .join("");

  modalBody.innerHTML = `
    ${mod.thumbnail_url ? `<img class="modal__hero" src="${mod.thumbnail_url}" alt="${mod.name}">` : ""}
    <div class="modal__body">
      <div class="modal__title">${mod.name}</div>
      <div class="modal__author">by ${mod.author || "Unknown"}</div>
      <div class="modal__stats">
        ${mod.rating != null ? `<span>Rating: <strong class="rating ${rc}">${Math.round(mod.rating)}%</strong></span>` : ""}
        ${mod.size_bytes ? `<span>Size: <strong>${formatBytes(mod.size_bytes)}</strong></span>` : ""}
        ${mod.download_count ? `<span>Downloads: <strong>${mod.download_count.toLocaleString()}</strong></span>` : ""}
        ${mod.created_at ? `<span>Created: <strong>${timeAgo(mod.created_at)}</strong></span>` : ""}
        ${mod.updated_at ? `<span>Updated: <strong>${timeAgo(mod.updated_at)}</strong></span>` : ""}
      </div>
      ${mod.description ? `<div class="modal__description">${mod.description}</div>` : ""}
      ${gallery ? `<div class="modal__gallery">${gallery}</div>` : ""}
      <div class="modal__actions">
        <a class="btn btn-primary" href="${mod.workshop_url || "#"}" target="_blank" rel="noopener">
          Open on Workshop ↗
        </a>
        <button class="btn btn-secondary" id="copy-id-btn" data-id="${mod.id}">
          Copy Mod ID
        </button>
      </div>
      <div class="updated-indicator">Mod ID: ${mod.id}</div>
    </div>`;

  document.getElementById("copy-id-btn")?.addEventListener("click", function () {
    copyToClipboard(this.dataset.id, this);
  });
}

document.getElementById("modal-close").addEventListener("click", () => {
  modal.classList.remove("open");
});

modal.addEventListener("click", e => {
  if (e.target === modal) modal.classList.remove("open");
});

// ── Sort ───────────────────────────────────────────────────────────────────
sortItems.forEach(item => {
  item.addEventListener("click", () => {
    sortItems.forEach(i => i.classList.remove("active"));
    item.classList.add("active");
    state.sort = item.dataset.sort;
    loadMods(true);
  });
});

// ── Search ─────────────────────────────────────────────────────────────────
searchInput.addEventListener("input", debounce(e => {
  state.search = e.target.value.trim();
  loadMods(true);
}, 300));

// ── Infinite scroll ────────────────────────────────────────────────────────
function setupIntersectionObserver() {
  const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) loadMods();
  }, { rootMargin: "200px" });
  observer.observe(sentinel);
}
