import { render, screen, fireEvent, waitFor } from '@testing-library/svelte'
import App from './App.svelte'
import { vi } from 'vitest'

describe('App', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })

  it('renders title', () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ reports: [] }) })
    render(App)
    expect(screen.getByText('Bandcamp Parser')).toBeInTheDocument()
  })

  it('shows error when url empty', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ reports: [] }) })
    render(App)
    await fireEvent.click(screen.getByText('Parse'))
    expect(screen.getByText('URL is required')).toBeInTheDocument()
  })

  it('parses release and shows title', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ reports: [] }) }) // onMount
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          url: 'u',
          title: 'In Rainbows',
          artist: 'Radiohead',
          type: 'album',
          cover_image_url: null,
          release_date: 'x',
          price: 9.99,
          currency: 'USD',
          about: null,
          credits: null,
          tracks: [{ track_num: 1, title: '15 Step', duration: 237 }],
          errors: [],
        }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ reports: [] }) }) // reload reports

    render(App)
    const input = screen.getByPlaceholderText('https://artist.bandcamp.com/album/...')
    await fireEvent.input(input, { target: { value: 'https://radiohead.bandcamp.com/album/in-rainbows' } })
    await fireEvent.click(screen.getByText('Parse'))
    await waitFor(() => expect(screen.getByText('In Rainbows')).toBeInTheDocument())
    expect(screen.getByText('Radiohead')).toBeInTheDocument()
  })
})
