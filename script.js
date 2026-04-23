document.addEventListener('DOMContentLoaded', () => {
    let currentCategory = 'MARKET';
    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');
    const updateTimeEl = document.getElementById('last-updated-time');
    const today = new Date();
    
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    dateEl.innerText = today.toLocaleDateString('ko-KR', options);

    function init() {
        if (typeof newsData !== 'undefined' && newsData) {
            // 갱신 시간 표시
            if (newsData.last_updated) {
                updateTimeEl.innerText = newsData.last_updated;
            }
            
            // 데이터 렌더링
            if (newsData.categories && Object.keys(newsData.categories).length > 0) {
                render(currentCategory);
            } else {
                showError("데이터가 비어 있습니다.");
            }
        } else {
            showError("데이터를 불러올 수 없습니다.");
        }
    }

    function showError(msg) {
        grid.innerHTML = `<div class="loading-state"><p>${msg} scraper.py를 실행해 주세요.</p></div>`;
    }

    function render(category) {
        grid.innerHTML = '';
        // 새로운 데이터 구조 (newsData.categories[category]) 대응
        const articles = (newsData.categories && newsData.categories[category]) || [];
        
        if (articles.length === 0) {
            grid.innerHTML = `<div class="loading-state"><p>현재 등록된 금융 뉴스가 없습니다.</p></div>`;
            return;
        }

        articles.forEach(item => {
            const card = document.createElement('article');
            card.className = 'news-card';
            card.onclick = () => window.open(item.link, '_blank');
            
            const publisher = item.publisher || 'Financial News';
            const summary = item.summary || '';
            const dateStr = item.date || '';

            card.innerHTML = `
                <div class="thumbnail-area">
                    <img src="${item.image}" alt="" loading="lazy" 
                        onerror="this.src='https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop'">
                </div>
                <div class="card-body">
                    <h2 class="article-title">${item.title}</h2>
                    <p class="article-summary">${summary}</p>
                    <div class="card-meta-info">
                        <span class="pub-name">${publisher}</span>
                        <span class="pub-date">${dateStr}</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
        
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