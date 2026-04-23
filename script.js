document.addEventListener('DOMContentLoaded', () => {
    let newsData = {};
    let currentCategory = 'TOP';

    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');

    // 오늘 날짜 표시
    const today = new Date();
    dateEl.innerText = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`;

    // GitHub CDN에서 실시간 데이터 가져오기
    const DATA_URL = 'https://cdn.jsdelivr.net/gh/hyundevvv/news@main/data.json';

    async function init() {
        try {
            const response = await fetch(DATA_URL + '?t=' + new Date().getTime());
            if (!response.ok) throw new Error('Network error');
            newsData = await response.json();
            console.log('Sync OK. Categories:', Object.keys(newsData));
            render(currentCategory);
        } catch (e) {
            console.error('Sync error:', e);
            grid.innerHTML = `<div class="loading-state"><p>데이터를 불러올 수 없습니다.</p></div>`;
        }
    }

    function render(category) {
        grid.innerHTML = '';
        const articles = newsData[category] || [];

        if (articles.length === 0) {
            grid.innerHTML = `<div class="loading-state"><p>해당 카테고리의 뉴스가 없습니다.</p></div>`;
            return;
        }

        articles.forEach(item => {
            const card = document.createElement('div');
            card.className = 'news-card';
            card.onclick = () => window.open(item.link, '_blank');

            // 날짜 포맷 MM.DD
            const dateObj = new Date(item.date);
            const dateStr = isNaN(dateObj)
                ? ''
                : `${String(dateObj.getMonth() + 1).padStart(2, '0')}.${String(dateObj.getDate()).padStart(2, '0')}`;

            card.innerHTML = `
                <div class="thumbnail-container">
                    <img src="${item.image}" alt="" loading="lazy"
                        onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=600&auto=format&fit=crop'">
                </div>
                <div class="content">
                    <h2 class="title">${item.title}</h2>
                    <div class="card-meta">
                        <span class="card-date">${dateStr}</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    // 탭 버튼 클릭
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