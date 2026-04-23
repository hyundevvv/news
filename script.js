document.addEventListener('DOMContentLoaded', () => {
    let currentCategory = 'MARKET';
    const grid = document.getElementById('news-grid');
    const updateTimeEl = document.getElementById('last-updated-time');
    const tickerWrapper = document.getElementById('ticker-wrapper');

    function init() {
        if (typeof newsData !== 'undefined' && newsData) {
            if (newsData.last_updated) updateTimeEl.textContent = newsData.last_updated;
            renderTicker(newsData.indices || []);
            if (newsData.categories) render(currentCategory);
        }
    }

    /**
     * XSS 방지를 위한 HTML 특수문자 치환 함수
     */
    function escapeHTML(str) {
        if (!str) return "";
        return str.replace(/[&<>"']/g, function(m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[m];
        });
    }

    function renderTicker(indices) {
        if (!indices || indices.length === 0) return;
        
        const content = indices.map(idx => {
            const isUp = idx.change.includes('+');
            const class_name = isUp ? 'up' : 'down';
            // 보안을 위해 각 필드 이스케이프 처리
            const safeName = escapeHTML(idx.name);
            const safePrice = escapeHTML(idx.price);
            const safeChange = escapeHTML(idx.change);

            return `
                <div class="ticker-item ${class_name}">
                    <span class="name">${safeName}</span>
                    <span class="price">${safePrice}</span>
                    <span class="change">${safeChange}</span>
                </div>
            `;
        }).join('');
        
        tickerWrapper.innerHTML = content + content;
    }

    function render(category) {
        grid.innerHTML = '';
        const articles = (newsData.categories && newsData.categories[category]) || [];
        
        articles.forEach(item => {
            const card = document.createElement('article');
            card.className = 'news-card';
            
            // 모든 외부 데이터 보안 처리
            const safeTitle = escapeHTML(item.title);
            const safeSummary = escapeHTML(item.summary);
            const safePub = escapeHTML(item.publisher);
            const safeDate = escapeHTML(item.date);
            const safeLink = escapeHTML(item.link);
            const safeImg = escapeHTML(item.image);

            card.innerHTML = `
                <button class="share-btn" title="링크 복사">
                    <svg viewBox="0 0 24 24"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92c0-1.61-1.31-2.92-2.92-2.92z"/></svg>
                </button>
                <div class="thumbnail-area" onclick="window.open('${safeLink}', '_blank')">
                    <img src="${safeImg}" alt="" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop'">
                </div>
                <div class="card-body" onclick="window.open('${safeLink}', '_blank')">
                    <h2 class="article-title">${safeTitle}</h2>
                    <p class="article-summary">${safeSummary}</p>
                    <div class="card-meta-info">
                        <span class="pub-name">${safePub}</span>
                        <span class="pub-date">${safeDate}</span>
                    </div>
                </div>
            `;

            card.querySelector('.share-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                copyToClipboard(item.link);
            });

            grid.appendChild(card);
        });
    }

    function copyToClipboard(text) {
        if (!text) return;
        navigator.clipboard.writeText(text).then(() => {
            alert('기사 링크가 복사되었습니다.');
        }).catch(err => {
            console.error('Copy failed', err);
        });
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelector('.tab-btn.active')?.classList.remove('active');
            btn.classList.add('active');
            currentCategory = btn.dataset.category;
            render(currentCategory);
        });
    });

    init();
});