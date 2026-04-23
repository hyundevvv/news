document.addEventListener('DOMContentLoaded', () => {
    // newsData는 data.js에서 전역 변수로 이미 선언되어 있습니다.
    let currentCategory = 'TOP';

    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');

    const today = new Date();
    dateEl.innerText = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`;

    function init() {
        console.log('Initializing H_NEWS...');
        
        // 전역 변수 newsData 확인
        if (typeof newsData !== 'undefined' && newsData && Object.keys(newsData).length > 0) {
            console.log('Data loaded from data.js:', Object.keys(newsData));
            render(currentCategory);
        } else {
            console.error('Data not found!');
            grid.innerHTML = `
                <div class="loading-state">
                    <p style="color:#f04452; font-weight:700;">⚠️ 데이터를 찾을 수 없습니다.</p>
                    <p style="font-size:0.85rem; margin-top:8px; line-height:1.6;">
                        scraper.py를 먼저 실행하여<br>데이터를 생성해 주세요.
                    </p>
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

            card.innerHTML = `
                <div class="thumbnail-container">
                    <img src="${item.image}" alt="" loading="lazy"
                        onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop'">
                </div>
                <div class="content">
                    <h2 class="title">${item.title}</h2>
                    <div class="card-meta">
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