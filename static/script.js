(() => {
  document.addEventListener('submit', (e) => e.preventDefault(), true);

  const descText   = document.getElementById('descText');
  const fileField  = document.getElementById('fileField');
  const preview    = document.getElementById('preview');
  const submitBtn  = document.getElementById('submitBtn');
  const statusEl   = document.getElementById('status');
  const captionBox = document.getElementById('captionBox');
  const captionOut = document.getElementById('captionOut');
  const resultsBox = document.getElementById('resultsBox');
  const resultsGrid= document.getElementById('resultsGrid');
  const searchSub  = document.getElementById('searchSub');
  const descWrap   = document.getElementById('descWrap');
  const fileWrap   = document.getElementById('fileWrap');

  const q = (sel) => document.querySelector(sel);
  function setStatus(msg) { statusEl.textContent = msg || ''; }
  function show(el) { el.classList.remove('hidden'); }
  function hide(el) { el.classList.add('hidden'); }
  function resetOutputs() {
    hide(captionBox);
    hide(resultsBox);
    captionOut.textContent = '';
    resultsGrid.innerHTML = '';
  }
  function resetFile() {
    fileField.value = '';
    preview.src = '';
    preview.style.display = 'none';
  }
  function currentMode() { return q('input[name="mode"]:checked')?.value || 'search'; }
  function currentSearchMode() { return q('input[name="searchMode"]:checked')?.value || 'desc'; }

  function imageBytesToUrl(image_bytes, mime = 'image/jpeg') {
    if (!image_bytes) return '';
    if (typeof image_bytes === 'string') {
      if (image_bytes.startsWith('data:')) return image_bytes; 
      return `data:${mime};base64,${image_bytes}`;
    }
    try {
      const u8 = new Uint8Array(image_bytes);
      const blob = new Blob([u8], { type: mime });
      return URL.createObjectURL(blob);
    } catch { return ''; }
  }

  function normalizeItems(items, fallbackTag = '') {
    return (items || []).map((it, i) => {
      const thumb = it.image_url || imageBytesToUrl(it.image_bytes, it.mime || 'image/jpeg');
      const title = it.caption || it.title || `Result ${i+1}${fallbackTag ? ' • ' + fallbackTag : ''}`;
      return { thumb, title };
    }).filter(x => !!x.thumb);
  }

  async function searchByDescription(query) {
    const res = await fetch("http://localhost:8000/search-by-description", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: query })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function searchByImage(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("http://localhost:8000/search-by-image", { method: "POST", body: fd });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function captionImage(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("http://localhost:8000/caption-image", { method: "POST", body: fd });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function syncUI() {
    const mode = currentMode();
    const searchBy = currentSearchMode();

    if (mode === 'search') {
      show(searchSub);
      if (searchBy === 'desc') { show(descWrap); hide(fileWrap); }
      else { hide(descWrap); show(fileWrap); }
    } else {
      hide(searchSub); hide(descWrap); show(fileWrap);
    }
    descText.disabled = !(mode === 'search' && searchBy === 'desc');
    fileField.disabled = !((mode === 'search' && searchBy === 'img') || mode === 'caption');
  }

  function renderResults(items) {
    resultsGrid.innerHTML = '';
    if (!items?.length) {
      resultsGrid.innerHTML = '<div class="muted">No results.</div>';
      return;
    }
    const frag = document.createDocumentFragment();
    for (const it of items) {
      const card = document.createElement('div');
      card.className = 'card';

      const img = document.createElement('img');
      img.src = it.thumb;
      img.alt = it.title || 'result';

      const meta = document.createElement('div');
      meta.className = 'meta';
      meta.textContent = it.title || 'Untitled';

      card.appendChild(img);
      card.appendChild(meta);
      frag.appendChild(card);
    }
    resultsGrid.appendChild(frag);
  }

  fileField.addEventListener('change', () => {
    const file = fileField.files?.[0];
    if (!file) { preview.src=''; preview.style.display='none'; return; }
    const url = URL.createObjectURL(file);
    preview.src = url;
    preview.style.display = 'block';
  });

  document.getElementById('formLike').addEventListener('change', (e) => {
    if (e.target.name === 'mode' || e.target.name === 'searchMode') {
      resetOutputs();
      setStatus('');
      if (e.target.name === 'mode') { descText.value = ''; resetFile(); }
      else if (e.target.name === 'searchMode') { resetFile(); descText.value = ''; }
      syncUI();
    }
  });

  async function handleRun() {
    resetOutputs();
    const mode = currentMode();
    const searchBy = currentSearchMode();

    try {
      submitBtn.disabled = true;

        if (searchBy === 'desc') {
          const qv = (descText.value || '').trim();
          if (!qv) { setStatus('Please enter a description.'); return; }
          setStatus('Searching by description…');

          const data = await searchByDescription(qv);

          const thumb =
            data.image_url ||
            imageBytesToUrl(data.image_bytes, data.mime || 'image/jpeg');

          if (!thumb) {
            setStatus('No image returned.');
            return;
          }

          const items = [{ thumb, title: data.caption || 'No caption' }];
          renderResults(items);
          show(resultsBox);
          setStatus('Found 1 result.');
        } else {
        const file = fileField.files?.[0];
        if (!file) { setStatus('Please choose an image to caption.'); return; }
        setStatus('Generating caption…');
        const { caption } = await captionImage(file);
        captionOut.textContent = caption || '(No caption)';
        show(captionBox);
        setStatus('Done.');
      }
    } catch (err) {
      console.error(err);
      setStatus('Something went wrong. Please try again.');
    } finally {
      submitBtn.disabled = false;
    }
  }

  submitBtn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); handleRun(); });
  descText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); handleRun(); }
  });

  syncUI();
})();
