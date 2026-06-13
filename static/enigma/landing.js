// Enigma TV - Landing Page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const player = document.getElementById('player');
    const channelList = document.getElementById('channel-list');
    const searchInput = document.getElementById('search');
    const groupSelect = document.getElementById('group-select');
    const channelCount = document.getElementById('channel-count');
    const nowPlayingName = document.getElementById('now-playing-name');
    const liveBadge = document.querySelector('.live-badge');
    const placeholder = document.getElementById('player-placeholder');
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menu-toggle');
    const sidebarClose = document.getElementById('sidebar-close');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    let channels = [];
    let currentChannel = null;
    let groups = new Set();

    // Load channels from backend
    loadChannels();

    // Mobile menu handlers
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.add('visible');
            sidebarOverlay.classList.add('active');
        });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    function closeSidebar() {
        sidebar.classList.remove('visible');
        sidebarOverlay.classList.remove('active');
    }

    async function loadChannels() {
        try {
            // Load the pre-configured playlist from backend
            const response = await fetch('/api/playlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: '/static/iptv_list.m3u8' })
            });

            if (!response.ok) throw new Error('Error al cargar canales');

            const data = await response.json();
            channels = data.channels || [];
            
            // Extract groups
            channels.forEach(ch => {
                if (ch.group && ch.group !== 'Sin grupo') {
                    groups.add(ch.group);
                }
            });

            populateGroupFilter();
            renderChannels(channels);
            updateChannelCount();

        } catch (error) {
            console.error('Error:', error);
            channelList.innerHTML = '<li class="channel-item" style="justify-content: center; color: var(--text-muted);">Error al cargar canales</li>';
        }
    }

    function populateGroupFilter() {
        groupSelect.innerHTML = '<option value="">Todos los canales</option>';
        Array.from(groups).sort().forEach(group => {
            const option = document.createElement('option');
            option.value = group;
            option.textContent = group;
            groupSelect.appendChild(option);
        });
    }

    function renderChannels(channelListData) {
        if (channelListData.length === 0) {
            channelList.innerHTML = '<li class="channel-item" style="justify-content: center; color: var(--text-muted);">No se encontraron canales</li>';
            return;
        }

        channelList.innerHTML = channelListData.map(channel => `
            <li class="channel-item ${currentChannel && currentChannel.url === channel.url ? 'active' : ''}"
                data-url="${escapeHtml(channel.url)}"
                data-name="${escapeHtml(channel.name)}">
                <div class="channel-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                </div>
                <div class="channel-info">
                    <div class="channel-name">${escapeHtml(channel.name)}</div>
                    <div class="channel-group">${escapeHtml(channel.group || 'General')}</div>
                </div>
                <div class="channel-status"></div>
            </li>
        `).join('');

        // Add click listeners
        document.querySelectorAll('.channel-item').forEach(item => {
            item.addEventListener('click', () => {
                const url = item.dataset.url;
                const name = item.dataset.name;
                playChannel(url, name);
                // Close sidebar on mobile after selection
                if (window.innerWidth <= 767) {
                    closeSidebar();
                }
            });
        });
    }

    function playChannel(url, name) {
        currentChannel = { url, name };

        // Update UI
        document.querySelectorAll('.channel-item').forEach(item => {
            item.classList.toggle('active', item.dataset.url === url);
        });

        // Update now playing
        nowPlayingName.textContent = name;
        nowPlayingName.classList.add('active');
        liveBadge.classList.add('visible');

        // Hide placeholder
        placeholder.classList.add('hidden');

        // Play through proxy or directly
        let playUrl = url;
        try {
            const hostname = new URL(url).hostname;
            if (!(hostname.endsWith('.dps.live') || 
                  hostname.endsWith('.dpsgo.com') || 
                  hostname.endsWith('.rudo.video') || 
                  hostname.endsWith('.mdstrm.com'))) {
                playUrl = `/stream?url=${encodeURIComponent(url)}`;
            }
        } catch(e) {
            playUrl = `/stream?url=${encodeURIComponent(url)}`;
        }
        player.src = playUrl;
        player.load();
        player.play().catch(err => console.log('Autoplay blocked:', err));
    }

    function updateChannelCount() {
        channelCount.textContent = channels.length;
    }

    function filterChannels() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        const selectedGroup = groupSelect.value;

        let filtered = channels;

        if (searchTerm) {
            filtered = filtered.filter(ch => 
                ch.name.toLowerCase().includes(searchTerm) ||
                (ch.group && ch.group.toLowerCase().includes(searchTerm))
            );
        }

        if (selectedGroup) {
            filtered = filtered.filter(ch => ch.group === selectedGroup);
        }

        renderChannels(filtered);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // Event listeners
    searchInput.addEventListener('input', filterChannels);
    groupSelect.addEventListener('change', filterChannels);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        
        switch (e.key) {
            case ' ':
                e.preventDefault();
                if (player.paused) {
                    player.play();
                } else {
                    player.pause();
                }
                break;
            case 'f':
                if (!document.fullscreenElement) {
                    player.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
                break;
            case 'ArrowDown':
                e.preventDefault();
                navigateChannel(1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                navigateChannel(-1);
                break;
            case 'Escape':
                closeSidebar();
                break;
        }
    });

    function navigateChannel(direction) {
        const items = document.querySelectorAll('.channel-item');
        const activeIndex = Array.from(items).findIndex(item => item.classList.contains('active'));
        
        let newIndex = activeIndex + direction;
        if (newIndex < 0) newIndex = items.length - 1;
        if (newIndex >= items.length) newIndex = 0;

        items[newIndex].click();
        items[newIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
});