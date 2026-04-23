document.addEventListener('DOMContentLoaded', () => {
    let newsData = {};
    let currentCategory = 'TOP';

    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');

    const today = new Date();
    dateEl.innerText = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`;

    // 캐시 방지를 위해 타임스탬프 추가
    const DATA_URL = 'https://cdn.jsdelivr.net/gh/hyundevvv/news@main/data.json';

    async function init() {
        try {
            const response = await fetch(DATA_URL + '?v=' + Date.now(), { cache: 'no-store' });
            if (!response.ok) throw new Error('Network error');
            newsData = await response.json();
            
            console.log('Sync Complete:', Object.keys(newsData));
            
            // 데이터가 비어있지 않은지 확인
            if (Object.keys(newsData).length > 0) {
                render(currentCategory);
            } else {
                throw new Error('Empty data');
            }
        } catch (e) {
            console.error('Sync Error:', e);
            grid.innerHTML = `
                <div class="loading-state">
                    <p>뉴스를 불러오는 데 실패했습니다.</p>
                    <p style="font-size:0.8rem; margin-top:8px; opacity:0.6;">GitHub 데이터 동기화 대기 중...</p>
                </div>`;
        }
    }

    function render(category) {
        grid.innerHTML = '';
        const articles = newsData[category] || [];

        if (articles.length === 0) {
            grid.innerHTML = `<div class="loading-state"><p>이 카테고리의 뉴스가 아직 없습니다.</p></div>`;
            return;
        }

        articles.forEach(item => {
            const card = document.createElement('div');
            card.className = 'news-card';
            card.onclick = () => window.open(item.link, '_blank');

            // 수집된 날짜를 그대로 표시 (04.23 14:15 형태)
            const dateDisplay = item.date || '';

            card.innerHTML = `
                <div class="thumbnail-container">
                    <img src="${item.image}" alt="" loading="lazy"
                        onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop'">
                </div>
                <div class="content">
                    <h2 class="title">${item.title}</h2>
                    <div class="card-meta">
                        <span class="card-date">${dateDisplay}</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
        
        // 렌더링 후 스크롤을 상단으로
        window.scrollTo({ top: 0, behavior: 'smooth' });
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