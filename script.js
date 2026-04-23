document.addEventListener('DOMContentLoaded', () => {
    let newsData = {};
    let currentCountry = 'KR';

    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const menuBtn = document.getElementById('menu-btn');
    const grid = document.getElementById('news-grid');
    const dateEl = document.getElementById('current-date');

    // Display today's date
    const today = new Date();
    const formattedToday = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`;
    dateEl.innerText = formattedToday;

    // Sidebar toggle logic
    const toggleSidebar = () => {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    };

    menuBtn.addEventListener('click', toggleSidebar);
    overlay.addEventListener('click', toggleSidebar);

    // Initial fetch
    async function init() {
        try {
            const response = await fetch('data.json?t=' + new Date().getTime());
            if (!response.ok) throw new Error('Network error');
            newsData = await response.json();
            render(currentCountry);
        } catch (e) {
            console.error(e);
            grid.innerHTML = `<div class="loading-state"><p>Failed to sync data.</p></div>`;
        }
    }

    // Render articles for the selected country
    function render(country) {
        grid.innerHTML = '';
        const articles = newsData[country] || [];
        
        if (articles.length === 0) {
            grid.innerHTML = `<div class="loading-state"><p>No news available for this region.</p></div>`;
            return;
        }

        articles.forEach(item => {
            const card = document.createElement('div');
            card.className = 'news-card';
            card.onclick = () => window.open(item.link, '_blank');
            
            card.innerHTML = `
                <div class="thumbnail-container">
                    <img src="${item.image}" alt="" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop'">
                </div>
                <div class="content">
                    <h2 class="title">${item.title}</h2>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    // Country selection logic
    document.querySelectorAll('.sidebar-menu li').forEach(li => {
        li.addEventListener('click', () => {
            const activeLi = document.querySelector('.sidebar-menu li.active');
            if (activeLi) activeLi.classList.remove('active');
            
            li.classList.add('active');
            currentCountry = li.dataset.country;
            
            render(currentCountry);
            toggleSidebar();
        });
    });

    init();
});