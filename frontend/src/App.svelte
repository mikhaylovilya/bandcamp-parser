<script>
  import { onMount } from 'svelte'

  let url = ''
  let loading = false
  let error = ''
  let release = null
  let reports = []
  let reportsLoading = false
  let selectedReport = null

  async function loadReports() {
    reportsLoading = true
    try {
      const res = await fetch('/api/reports')
      if (!res.ok) throw new Error('Failed to load reports')
      const data = await res.json()
      reports = data.reports || []
    } catch (e) {
      error = e.message
    } finally {
      reportsLoading = false
    }
  }

  async function parse() {
    error = ''
    release = null
    if (!url.trim()) {
      error = 'URL is required'
      return
    }
    loading = true
    try {
      const res = await fetch('/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.message || 'Parse failed')
      }
      release = data
      await loadReports()
    } catch (e) {
      error = e.message
    } finally {
      loading = false
    }
  }

  async function viewReport(id) {
    error = ''
    try {
      const res = await fetch(`/api/reports/${id}`)
      if (!res.ok) throw new Error('Failed to load report')
      const data = await res.json()
      selectedReport = data
      release = data.data || data
    } catch (e) {
      error = e.message
    }
  }

  async function removeReport(id) {
    try {
      const res = await fetch(`/api/reports/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Delete failed')
      reports = reports.filter((r) => r.id !== id)
      if (release && release.url) {
        // keep current view
      }
    } catch (e) {
      error = e.message
    }
  }

  onMount(loadReports)
</script>

<main>
  <h1>Bandcamp Parser</h1>

  <section class="input">
    <input type="url" bind:value={url} placeholder="https://artist.bandcamp.com/album/..." />
    <button on:click={parse} disabled={loading}>{loading ? 'Parsing...' : 'Parse'}</button>
  </section>

  {#if error}
    <p class="error">{error}</p>
  {/if}

  {#if release}
    <section class="card">
      {#if release.cover_image_url}
        <div class="cover">
          <img src={release.cover_image_url} alt={release.title} />
        </div>
      {/if}
      <h2>{release.title}</h2>
      <p class="artist">{release.artist}</p>
      <p class="meta">{release.type} · {release.release_date || '—'} · {release.price != null ? release.price + ' ' + (release.currency || '') : '—'}</p>
      {#if release.description}
        <p class="desc">{release.description}</p>
      {/if}
      {#if release.about}
        <p class="about">{release.about}</p>
      {/if}
      {#if release.lyrics}
        <pre class="lyrics">{release.lyrics}</pre>
      {/if}
      {#if release.tracks && release.tracks.length}
        <ol class="tracks">
          {#each release.tracks as t}
            <li>{t.title} {t.duration ? '(' + Math.round(t.duration) + 's)' : ''}</li>
          {/each}
        </ol>
      {/if}
      {#if release.comments && release.comments.length}
        <div class="comments">
          <h3>Top comments</h3>
          <ul>
            {#each release.comments as c}
              <li><strong>{c.author || 'anon'}</strong>: {c.text}</li>
            {/each}
          </ul>
        </div>
      {/if}
      {#if release.errors && release.errors.length}
        <div class="errors">
          <h3>Parsing errors</h3>
          <ul>
            {#each release.errors as e}
              <li>{e}</li>
            {/each}
          </ul>
        </div>
      {/if}
    </section>
  {/if}

  <section class="reports">
    <h2>Saved reports</h2>
    {#if reportsLoading}
      <p>Loading...</p>
    {:else if reports.length === 0}
      <p>No reports yet.</p>
    {:else}
      <ul>
        {#each reports as r (r.id)}
          <li>
            <button class="link" on:click={() => viewReport(r.id)}>{r.title || r.url} — {r.artist || ''}</button>
            <button on:click={() => removeReport(r.id)}>Delete</button>
          </li>
        {/each}
      </ul>
    {/if}
  </section>
</main>

<style>
  main { max-width: 100%; }
  h1 { font-size: 1.8rem; margin: 0 0 1rem; }
  h2 { font-size: 1.25rem; margin: 1.25rem 0 0.5rem; }
  h3 { font-size: 1rem; margin: 0.75rem 0 0.25rem; }
  .link { background: none; border: none; color: var(--accent); cursor: pointer; padding: 0; text-align: left; font: inherit; }
  .link:hover { color: var(--accent-hover); text-decoration: underline; }
  .input { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
  .input input { flex: 1 1 260px; }
  .card { background: var(--surface); border: 1px solid var(--border); padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: var(--shadow); }
  .cover { text-align: center; margin-bottom: 0.75rem; }
  .cover img { max-width: 220px; border-radius: 10px; box-shadow: var(--shadow); }
  .artist { color: var(--text-muted); margin: 0 0 0.25rem; }
  .meta { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 0.5rem; }
  .desc { margin: 0.5rem 0; }
  .about { margin: 0.5rem 0; color: var(--text-muted); font-style: italic; }
  .lyrics { white-space: pre-wrap; background: var(--code-bg); padding: 0.75rem; border-radius: 8px; font-family: var(--mono); font-size: 0.9rem; }
  .error { color: var(--danger); }
  .errors { color: #b45309; }
  .comments ul { padding-left: 1.25rem; }
  .tracks { margin: 0.5rem 0; padding-left: 1.5rem; text-align: left; list-style: decimal; }
  .reports ul { list-style: none; padding: 0; }
  .reports li { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; padding: 0.4rem 0; border-bottom: 1px solid var(--border); }
</style>
