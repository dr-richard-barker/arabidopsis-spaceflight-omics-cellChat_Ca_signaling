/* ==========================================================================
   Integrated Manuscript PDF Viewer
   - Accessible tablist with ArrowLeft/ArrowRight/Home/End keyboard support
   - Native desktop <iframe> PDF viewer for instant search & vector crispness
   - Optional / automatic mobile PDF.js canvas reader fallback (via pdfjs-dist)
   ========================================================================== */
(() => {
  const root = document.getElementById("manuscript-reader");
  if (!root) return;

  const tabs = Array.from(root.querySelectorAll('[role="tab"]'));
  const panels = Array.from(root.querySelectorAll('[role="tabpanel"]'));
  const openBtn = root.querySelector("[data-pdf-open]");
  const dlPdfBtn = root.querySelector("[data-pdf-download]");
  const dlDocxBtn = root.querySelector("[data-docx-download]");
  const modeToggleBtn = root.querySelector("[data-mode-toggle]");
  const statusBadge = root.querySelector("[data-doc-meta]");

  const isCoarsePointer = window.matchMedia("(pointer: coarse)").matches;
  let useCanvasMode = isCoarsePointer;
  let pdfjsLibPromise = null;

  const PDFJS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.6.82/pdf.min.mjs";
  const PDFJS_WORKER = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.6.82/pdf.worker.min.mjs";

  function loadPdfJs() {
    if (!pdfjsLibPromise) {
      pdfjsLibPromise = import(PDFJS_CDN).then((lib) => {
        lib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER;
        return lib;
      });
    }
    return pdfjsLibPromise;
  }

  function updateToolbarLinks(tab) {
    const pdfUrl = tab.dataset.pdf;
    const docxUrl = tab.dataset.docx;
    const metaText = tab.dataset.meta || "";
    if (openBtn) openBtn.href = pdfUrl;
    if (dlPdfBtn) dlPdfBtn.href = pdfUrl;
    if (dlDocxBtn) {
      if (docxUrl) {
        dlDocxBtn.href = docxUrl;
        dlDocxBtn.hidden = false;
      } else {
        dlDocxBtn.hidden = true;
      }
    }
    if (statusBadge) statusBadge.textContent = metaText;
  }

  async function renderCanvasViewer(panel, pdfUrl) {
    const shell = panel.querySelector(".pdfjs-shell");
    if (!shell) return;
    const wrap = shell.querySelector(".pdfjs-canvas-wrap");
    const pageLabel = shell.querySelector("[data-page-label]");
    const prevBtn = shell.querySelector("[data-page-prev]");
    const nextBtn = shell.querySelector("[data-page-next]");
    const zoomInBtn = shell.querySelector("[data-zoom-in]");
    const zoomOutBtn = shell.querySelector("[data-zoom-out]");

    if (shell.dataset.loadedUrl === pdfUrl) return;
    wrap.innerHTML = '<div class="pdfjs-status">Loading PDF pages…</div>';

    try {
      const pdfjsLib = await loadPdfJs();
      const doc = await pdfjsLib.getDocument(pdfUrl).promise;
      shell.dataset.loadedUrl = pdfUrl;

      let currentPage = 1;
      let scale = window.innerWidth < 700 ? 1.1 : 1.35;

      async function drawPage(num) {
        currentPage = Math.max(1, Math.min(num, doc.numPages));
        const page = await doc.getPage(currentPage);
        const viewport = page.getViewport({ scale });
        const dpr = Math.min(window.devicePixelRatio || 1, 2);

        const canvas = document.createElement("canvas");
        canvas.width = Math.floor(viewport.width * dpr);
        canvas.height = Math.floor(viewport.height * dpr);
        canvas.style.width = `${Math.floor(viewport.width)}px`;

        const ctx = canvas.getContext("2d");
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        await page.render({ canvasContext: ctx, viewport }).promise;

        wrap.innerHTML = "";
        wrap.appendChild(canvas);
        if (pageLabel) pageLabel.textContent = `Page ${currentPage} of ${doc.numPages}`;
        if (prevBtn) prevBtn.disabled = currentPage <= 1;
        if (nextBtn) nextBtn.disabled = currentPage >= doc.numPages;
      }

      if (prevBtn) prevBtn.onclick = () => drawPage(currentPage - 1);
      if (nextBtn) nextBtn.onclick = () => drawPage(currentPage + 1);
      if (zoomInBtn) zoomInBtn.onclick = () => { scale = Math.min(scale + 0.25, 2.5); drawPage(currentPage); };
      if (zoomOutBtn) zoomOutBtn.onclick = () => { scale = Math.max(scale - 0.25, 0.75); drawPage(currentPage); };

      await drawPage(1);
    } catch (err) {
      wrap.innerHTML =
        `<div class="pdfjs-status">Inline canvas preview unavailable offline or blocked. ` +
        `<a href="${pdfUrl}" target="_blank" rel="noopener">Open PDF in a new tab</a>.</div>`;
    }
  }

  function syncPanelMode(panel, pdfUrl) {
    const iframe = panel.querySelector(".pdf-frame");
    const canvasShell = panel.querySelector(".pdfjs-shell");
    if (!iframe || !canvasShell) return;

    if (useCanvasMode) {
      iframe.hidden = true;
      canvasShell.hidden = false;
      renderCanvasViewer(panel, pdfUrl);
    } else {
      canvasShell.hidden = true;
      iframe.hidden = false;
      if (!iframe.getAttribute("src")) {
        iframe.setAttribute("src", `${pdfUrl}#view=FitH`);
      }
    }
  }

  function selectTab(targetTab, focusTab = false) {
    const targetId = targetTab.id;
    tabs.forEach((t) => {
      const selected = t === targetTab;
      t.setAttribute("aria-selected", selected ? "true" : "false");
      t.tabIndex = selected ? 0 : -1;
    });

    panels.forEach((p) => {
      const match = p.getAttribute("aria-labelledby") === targetId;
      p.hidden = !match;
      if (match) {
        p.tabIndex = 0;
        syncPanelMode(p, targetTab.dataset.pdf);
      } else {
        p.removeAttribute("tabindex");
      }
    });

    updateToolbarLinks(targetTab);
    if (focusTab) {
      targetTab.focus();
      targetTab.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  tabs.forEach((tab, idx) => {
    tab.addEventListener("click", () => selectTab(tab, false));
    tab.addEventListener("keydown", (e) => {
      let nextIdx = null;
      if (e.key === "ArrowRight") nextIdx = (idx + 1) % tabs.length;
      else if (e.key === "ArrowLeft") nextIdx = (idx - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") nextIdx = 0;
      else if (e.key === "End") nextIdx = tabs.length - 1;
      if (nextIdx !== null) {
        e.preventDefault();
        selectTab(tabs[nextIdx], true);
      }
    });
  });

  if (modeToggleBtn) {
    const refreshToggleText = () => {
      modeToggleBtn.textContent = useCanvasMode ? "Use Browser PDF" : "Canvas Reader (Mobile/Zoom)";
      modeToggleBtn.classList.toggle("is-active", useCanvasMode);
      modeToggleBtn.setAttribute("aria-pressed", useCanvasMode ? "true" : "false");
    };
    refreshToggleText();
    modeToggleBtn.addEventListener("click", () => {
      useCanvasMode = !useCanvasMode;
      refreshToggleText();
      const activeTab = tabs.find((t) => t.getAttribute("aria-selected") === "true") || tabs[0];
      if (activeTab) selectTab(activeTab, false);
    });
  }

  // Initialize first selected tab
  const initialTab = tabs.find((t) => t.getAttribute("aria-selected") === "true") || tabs[0];
  if (initialTab) selectTab(initialTab, false);
})();
