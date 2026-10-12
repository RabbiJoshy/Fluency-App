// Song provenance shared by live cards and their tutorial replicas.
export function songCreditHTML(song, artist = '') {
    const escape = value => String(value || '').replace(/[&<>"']/g,
        ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]));
    return `<span class="example-song-credit example-song-credit--stacked"><span class="example-song-title">${escape(song)}</span>${artist ? `<span class="example-vocalist-credit example-song-artist">${escape(Array.isArray(artist) ? artist.join(' & ') : artist)}</span>` : ''}</span>`;
}
