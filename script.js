document.addEventListener('DOMContentLoaded', () => {
    let currentCategory = 'TOP';
    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');
    const today = new Date();
    
    // 헤더 날짜 표시 (요일 포함)
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    dateEl.innerText = today.toLocaleDateString('ko-KR', options);

    function init() {
        if (typeof newsData !== 'undefined' && newsData && Object.keys(newsData).length > 0) {
            render(currentCategory);
        } else {
            grid.innerHTML = `<div class="loading-state"><p>뉴스 데이터를 불러오는 중입니다...</p></div>`;
        }
    }

    function render(category) {
        grid.innerHTML = '';
        const articles = newsData[category] || [];
        
        if (articles.length === 0) {
            grid.innerHTML = `<div class="loading-state"><p>현재 등록된 기사가 없습니다.</p></div>`;
            return;
        }

        articles.forEach(item => {
            const card = document.createElement('article');
            card.className = 'news-card';
            card.onclick = () => window.open(item.link, '_blank');
            
            const publisher = item.publisher || 'Global News';
            const dateStr = item.date || '';

            card.innerHTML = `
                <div class="thumbnail-area">
                    <img src="${item.image}" alt="" loading="lazy" 
                        onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop'">
                </div>
                <div class="card-body">
                    <div class="category-label">${category}</div>
                    <h2 class="article-title">${item.title}</h2>
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