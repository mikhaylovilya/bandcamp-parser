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
      {#if release.cover_image_url}
        <img src={release.cover_image_url} alt={release.title} />
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
  main { max-width: 800px; margin: 0 auto; padding: 1rem; font-family: system-ui, sans-serif; text-align: left; }
  .link { background: none; border: none; color: #1a0dab; cursor: pointer; padding: 0; text-align: left; }
  .input { display: flex; gap: .5rem; margin-bottom: 1rem; }
  input { flex: 1; padding: .5rem; }
  .card { border: 1px solid #ddd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
  .card img { max-width: 200px; }
  .error { color: #c00; }
  .errors { color: #a60; }
  .tracks { margin: .5rem 0; padding-left: 1.5rem; text-align: left; list-style: decimal; }
  .reports ul { list-style: none; padding: 0; }
  .reports li { display: flex; justify-content: space-between; padding: .25rem 0; }
</style>
