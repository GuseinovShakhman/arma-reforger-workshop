/**
 * api.js — Fetch helpers for the Workshop Mirror API.
 */

const API_BASE = window.API_BASE || "";

/**
 * Fetch a paginated list of mods.
 * @param {Object} params — { search, tags, sort, page, limit }
 */
export async function fetchMods({ search = "", tags = [], sort = "newest", page = 1, limit = 24 } = {}) {
  const qs = new URLSearchParams();
  if (search)       qs.set("search", search);
  if (tags.length)  qs.set("tags", tags.join(","));
  if (sort)         qs.set("sort", sort);
  qs.set("page",  String(page));
  qs.set("limit", String(limit));

  const res = await fetch(`${API_BASE}/api/mods?${qs}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json(); // ModListResponse
}

/**
 * Fetch full detail for a single mod.
 * @param {string} modId
 */
export async function fetchMod(modId) {
  const res = await fetch(`${API_BASE}/api/mods/${encodeURIComponent(modId)}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json(); // ModDetail
}

/**
 * Fetch all tags with counts.
 */
export async function fetchTags() {
  const res = await fetch(`${API_BASE}/api/tags`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json(); // TagCount[]
}

/**
 * Fetch global stats.
 */
export async function fetchStats() {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json(); // StatsResponse
}
