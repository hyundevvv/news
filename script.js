document.addEventListener('DOMContentLoaded', () => {
    let newsData = {};
    let currentCategory = 'TOP';

    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');

    const today = new Date();
    dateEl.innerText = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`;

    // [중요] 로컬 환경과 배포 환경 분기 처리
    const isLocal = location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.protocol === 'file:';
    const DATA_URL = isLocal ? './data.json' : 'https://cdn.jsdelivr.net/gh/hyundevvv/news@main/data.json';

    console.log('Fetching from:', DATA_URL);

    async function init() {
        try {
            // 캐시 방지를 위해 타임스탬프 추가
            const response = await fetch(DATA_URL + (DATA_URL.includes('?') ? '&' : '?') + 't=' + Date.now(), {
                cache: 'no-store'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }
            
            const text = await response.text();
            try {
                newsData = JSON.parse(text);
            } catch (jsonErr) {
                console.error('JSON Parse Error. Raw text:', text.substring(0, 100));
                throw new Error('JSON 파일 형식이 올바르지 않습니다.');
            }

            console.log('Data Loaded Successfully:', Object.keys(newsData));
            
            if (Object.keys(newsData).length === 0) {
                throw new Error('데이터가 비어 있습니다.');
            }
            
            render(currentCategory);
        } catch (e) {
            console.error('Final Error:', e);
            grid.innerHTML = `
                <div class="loading-state">
                    <p style="color:#f04452; font-weight:700;">⚠️ 연결 오류</p>
                    <p style="font-size:0.85rem; margin-top:8px; line-height:1.6;">
                        ${e.message}<br>
                        <span style="opacity:0.6;">(콘솔창 F12를 확인해 주세요)</span>
                    </p>
                    <button onclick="location.reload()" style="margin-top:20px; padding:10px 20px; border-radius:12px; border:none; background:#3182f6; color:#fff; font-weight:600;">다시 시도</button>
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