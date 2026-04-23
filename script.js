document.addEventListener('DOMContentLoaded', () => {
    let currentCategory = 'TOP';
    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');
    const today = new Date();
    dateEl.innerText = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`;

    function init() {
        if (typeof newsData !== 'undefined' && newsData && Object.keys(newsData).length > 0) {
            render(currentCategory);
        } else {
            grid.innerHTML = `<div class="loading-state"><p>데이터를 불러올 수 없습니다. scraper.py를 실행해 주세요.</p></div>`;
        }
    }

    function render(category) {
        grid.innerHTML = '';
        const articles = newsData[category] || [];
        if (articles.length === 0) {
            grid.innerHTML = `<div class="loading-state"><p>기사가 없습니다.</p></div>`;
            return;
        }

        articles.forEach(item => {
            const card = document.createElement('div');
            card.className = 'news-card';
            card.onclick = () => window.open(item.link, '_blank');
            const publisher = item.publisher || 'Global News';

            card.innerHTML = `
                <div class="thumbnail-container">
                    <img src="${item.image}" alt="" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop'">
                </div>
                <div class="content">
                    <h2 class="title">${item.title}</h2>
                    <div class="card-footer">
                        <span class="publisher-tag">${publisher}</span>
                        <span class="card-date">${item.date || ''}</span>
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