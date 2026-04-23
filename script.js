document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('news-grid');

    async function fetchNews() {
        try {
            // Using cache busting to ensure we always get the latest news
            const response = await fetch('data.json?t=' + new Date().getTime());
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            renderNews(data);
        } catch (error) {
            console.error('Fetch error:', error);
            grid.innerHTML = `<p class="error">Failed to synchronize with the universe. Please try again later.</p>`;
        }
    }

    function renderNews(articles) {
        grid.innerHTML = ''; // Clear loading state

        articles.forEach(article => {
            const card = document.createElement('div');
            card.className = 'news-card';
            card.onclick = () => window.open(article.link, '_blank');

            // Format date (Google News usually gives 'Thu, 23 Apr 2026 01:23:45 GMT')
            const dateObj = new Date(article.date);
            const formattedDate = isNaN(dateObj.getTime()) ? article.date : `${dateObj.getMonth() + 1}.${dateObj.getDate()}`;

            card.innerHTML = `
                <div class="thumbnail-container">
                    <img src="${article.image}" alt="${article.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop'">
                </div>
                <div class="content">
                    <div>
                        <span class="category">${article.category}</span>
                        <h2 class="title">${article.title}</h2>
                    </div>
                    <span class="date">${formattedDate}</span>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    fetchNews();
});