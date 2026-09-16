(() => {
  'use strict';
  const config = window.YESF_CONFIG || {};
  const httpsURL = (value) => {
    if (typeof value !== 'string' || !value.trim()) return null;
    try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; }
    catch { return null; }
  };
  document.querySelectorAll('[data-config-link]').forEach((link) => {
    const url = httpsURL(config[link.dataset.configLink]);
    if (url) {
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.removeAttribute('aria-label');
    } else {
      const label = link.textContent.replace(/\s+/g, ' ').trim();
      link.setAttribute('aria-label', `${label}（準備中）`);
      link.addEventListener('click', (event) => {
        event.preventDefault();
        const target = document.querySelector(link.getAttribute('href'));
        if (target) target.textContent = link.dataset.pending;
      });
    }
  });
  const detailsReady = httpsURL(config.partnershipDetails);
  const applicationReady = httpsURL(config.partnershipApplication);
  const status = document.getElementById('partnership-status');
  if (detailsReady && applicationReady) status.hidden = true;
  else if (detailsReady) status.textContent = '協賛のお申し込み窓口は、近日公開予定です。';
  else if (applicationReady) status.textContent = '協賛資料は、近日公開予定です。';

  const list = document.getElementById('partner-list');
  if (Array.isArray(config.partners)) config.partners.forEach((partner) => {
    if (!partner || typeof partner.name !== 'string' || typeof partner.logo !== 'string') return;
    // Keep logos local to the static site; never interpret names or URLs as HTML.
    if (!/^assets\/partners\/[a-zA-Z0-9_.\/-]+\.(svg|png|webp|jpe?g)$/i.test(partner.logo) || partner.logo.includes('..')) return;
    const li = document.createElement('li');
    const img = document.createElement('img');
    img.src = partner.logo; img.alt = partner.name; img.loading = 'lazy'; img.width = 240; img.height = 90;
    const url = httpsURL(partner.url);
    if (url) { const link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.append(img); li.append(link); }
    else li.append(img);
    list.append(li);
  });
  document.getElementById('our-partners').hidden = !list.children.length;

  // Keep the usable profile link and fallback until X reports a rendered timeline.
  const box = document.getElementById('x-timeline');
  const fallback = document.getElementById('x-fallback');
  window.twttr = window.twttr || {};
  window.twttr._e = window.twttr._e || [];
  window.twttr.ready = window.twttr.ready || ((callback) => window.twttr._e.push(callback));
  window.twttr.ready((twitter) => {
    if (!twitter.events) return;
    twitter.events.bind('rendered', (event) => {
      if (event.target && box.contains(event.target)) {
        event.target.setAttribute('title', 'Yokosuka eGeneration 公式Xの投稿');
        fallback.hidden = true;
      }
    });
  });

  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if ('IntersectionObserver' in window && !motion.matches) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.remove('is-pending');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.06 });
    document.querySelectorAll('.reveal').forEach((element) => {
      if (element.getBoundingClientRect().top > window.innerHeight) element.classList.add('is-pending');
      observer.observe(element);
    });
    // Anchor navigation must immediately expose every requested section.
    document.querySelectorAll('a[href^="#"]').forEach((link) => link.addEventListener('click', () => {
      const target = document.getElementById(link.hash.slice(1));
      if (target) target.querySelectorAll('.is-pending').forEach((element) => element.classList.remove('is-pending'));
    }));
    motion.addEventListener('change', () => {
      if (motion.matches) document.querySelectorAll('.is-pending').forEach((element) => element.classList.remove('is-pending'));
    });
  }
})();
