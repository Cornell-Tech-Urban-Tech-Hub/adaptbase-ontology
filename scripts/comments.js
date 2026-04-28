(function () {
  const REPO_OWNER = 'Cornell-Tech-Urban-Tech-Hub';
  const REPO_NAME = 'adaptbase-ontology';
  const API_BASE = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}`;

  const cache = new Map();
  const CACHE_TTL = 5 * 60 * 1000;

  function esc(s) {
    return String(s ?? '').replace(/[&<>"]/g, c => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'
    }[c]));
  }

  function timeAgo(dateStr) {
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    const diff = now - then;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  function avatarColor(login) {
    const colors = ['carn', 'blue', 'green', 'slate', 'amber'];
    let hash = 0;
    for (let i = 0; i < login.length; i++) hash = ((hash << 5) - hash + login.charCodeAt(i)) | 0;
    return colors[Math.abs(hash) % colors.length];
  }

  function initials(name) {
    return (name || '??').split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();
  }

  function labelForKey(key) {
    return `ontology:${key}`;
  }

  function newIssueUrl(key, label) {
    const issueTitle = encodeURIComponent(`[Review] ${label}`);
    const issueBody = encodeURIComponent(
      `**Ontology element:** \`${key}\`\n**Label:** ${label}\n\n---\n\n_Your review comment here. Describe what you'd change, flag an ambiguity, or suggest an improvement._`
    );
    const issueLabel = encodeURIComponent(labelForKey(key));
    return `https://github.com/${REPO_OWNER}/${REPO_NAME}/issues/new?title=${issueTitle}&body=${issueBody}&labels=${issueLabel},review`;
  }

  function viewIssuesUrl(key) {
    const label = encodeURIComponent(labelForKey(key));
    return `https://github.com/${REPO_OWNER}/${REPO_NAME}/issues?q=is%3Aissue+label%3A${label}`;
  }

  async function fetchIssues(key) {
    const cached = cache.get(key);
    if (cached && Date.now() - cached.time < CACHE_TTL) return cached.data;

    const label = labelForKey(key);
    const url = `${API_BASE}/issues?labels=${encodeURIComponent(label)}&state=open&sort=created&direction=desc&per_page=20`;

    try {
      const res = await fetch(url, {
        headers: { 'Accept': 'application/vnd.github.v3+json' },
      });

      if (res.status === 403) {
        const remaining = res.headers.get('x-ratelimit-remaining');
        if (remaining === '0') {
          return { error: 'rate-limited' };
        }
      }

      if (!res.ok) return { error: `GitHub API returned ${res.status}` };

      const issues = await res.json();
      const result = { issues };
      cache.set(key, { data: result, time: Date.now() });
      return result;
    } catch (err) {
      return { error: err.message };
    }
  }

  async function fetchIssueComments(issueNumber) {
    const cacheKey = `comments:${issueNumber}`;
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.time < CACHE_TTL) return cached.data;

    const url = `${API_BASE}/issues/${issueNumber}/comments?per_page=50`;
    try {
      const res = await fetch(url, {
        headers: { 'Accept': 'application/vnd.github.v3+json' },
      });
      if (!res.ok) return [];
      const comments = await res.json();
      cache.set(cacheKey, { data: comments, time: Date.now() });
      return comments;
    } catch {
      return [];
    }
  }

  function renderIssueThread(issue, replies) {
    const color = avatarColor(issue.user.login);
    const ini = initials(issue.user.login);
    const issueUrl = issue.html_url;

    let html = `
      <div class="comment c-${color}">
        <div class="avatar">${ini}</div>
        <div class="bubble">
          <div class="byline">
            <a href="${esc(issue.user.html_url)}" target="_blank" rel="noopener" class="name" style="text-decoration:none;color:inherit;">${esc(issue.user.login)}</a>
            <span class="time">${timeAgo(issue.created_at)}</span>
          </div>
          <div class="body"><strong>${esc(issue.title.replace(/^\[Review\]\s*/, ''))}</strong></div>
          <div class="body">${renderMarkdownSimple(issue.body || '')}</div>
          <div class="actions">
            <a href="${esc(issueUrl)}" target="_blank" rel="noopener">View on GitHub</a>
            <a href="${esc(issueUrl)}" target="_blank" rel="noopener">Reply</a>
          </div>
        </div>
      </div>
    `;

    for (const reply of replies) {
      const rColor = avatarColor(reply.user.login);
      const rIni = initials(reply.user.login);
      html += `
        <div class="comment comment-reply c-${rColor}">
          <div class="avatar">${rIni}</div>
          <div class="bubble">
            <div class="byline">
              <a href="${esc(reply.user.html_url)}" target="_blank" rel="noopener" class="name" style="text-decoration:none;color:inherit;">${esc(reply.user.login)}</a>
              <span class="time">${timeAgo(reply.created_at)}</span>
            </div>
            <div class="body">${renderMarkdownSimple(reply.body || '')}</div>
          </div>
        </div>
      `;
    }

    return html;
  }

  function renderMarkdownSimple(text) {
    text = text.replace(/^---\s*$/gm, '');

    return esc(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code style="background:var(--sodium-soft);padding:1px 3px;border-radius:2px;">$1</code>')
      .replace(/\n/g, '<br>');
  }

  async function loadComments(containerEl) {
    const key = containerEl.dataset.commentKey;
    const label = containerEl.dataset.commentLabel;
    if (!key) return;

    containerEl.innerHTML = '<div class="comments-loading">Loading comments…</div>';

    const result = await fetchIssues(key);

    if (result.error) {
      const isRateLimit = result.error === 'rate-limited';
      containerEl.innerHTML = `
        <div class="comment-error">
          ${isRateLimit
            ? 'GitHub API rate limit reached.<br>Comments will reload shortly.'
            : 'Could not load comments.'}
        </div>
        <a class="comment-new-link" href="${esc(viewIssuesUrl(key))}" target="_blank" rel="noopener">
          View discussions on GitHub
        </a>
        <a class="comment-new-link" href="${esc(newIssueUrl(key, label))}" target="_blank" rel="noopener">
          + Start a new review thread
        </a>
      `;
      return;
    }

    const issues = result.issues || [];

    if (issues.length === 0) {
      containerEl.innerHTML = `
        <div class="empty-comments">
          No review comments yet on this ${key.includes(':') ? 'relationship' : 'entity'}.<br>
          Be the first — your feedback shapes the next version.
        </div>
        <a class="comment-new-link" href="${esc(newIssueUrl(key, label))}" target="_blank" rel="noopener">
          + Start a new review thread on GitHub
        </a>
      `;

      const badge = document.querySelector('.tab-btn[data-tab="comments"] .badge');
      if (badge) badge.textContent = '0';
      return;
    }

    let totalComments = issues.length;
    let threadsHtml = '';

    for (const issue of issues) {
      const replies = issue.comments > 0 ? await fetchIssueComments(issue.number) : [];
      totalComments += replies.length;
      threadsHtml += renderIssueThread(issue, replies);
    }

    containerEl.innerHTML = `
      <div class="comment-thread">
        ${threadsHtml}
      </div>
      <a class="comment-new-link" href="${esc(newIssueUrl(key, label))}" target="_blank" rel="noopener">
        + Start a new review thread on GitHub
      </a>
    `;

    const badge = document.querySelector('.tab-btn[data-tab="comments"] .badge');
    if (badge) badge.textContent = String(totalComments);
  }

  window.Comments = { loadComments };
})();
