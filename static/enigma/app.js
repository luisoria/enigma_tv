// Enigma TV - JavaScript Application

document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        currentView: 'home',
        currentChannel: null,
        playlists: [],
        channels: [],
        favorites: JSON.parse(localStorage.getItem('enigma_favorites') || '[]'),
        queue: [],
        activePlaylistUrl: null
    };
    let hlsInstance = null;

    // DOM Elements
    const elements = {
        // Navigation
        navBtns: document.querySelectorAll('.nav-btn'),
        menuToggle: document.getElementById('menu-toggle'),
        sidebar: document.querySelector('.sidebar'),
        
        // Views
        views: document.querySelectorAll('.view'),
        pageTitle: document.getElementById('page-title'),
        
        // Search
        searchInput: document.getElementById('search-input'),
        globalSearch: document.getElementById('global-search'),
        searchResults: document.getElementById('search-results'),
        
        // Channels
        homeChannels: document.getElementById('home-channels'),
        favoritesChannels: document.getElementById('favorites-channels'),
        
        // Player
        playerSidebar: document.getElementById('player-sidebar'),
        videoPlayer: document.getElementById('video-player'),
        currentChannelName: document.getElementById('current-channel-name'),
        currentChannelUrl: document.getElementById('current-channel-url'),
        closePlayer: document.getElementById('close-player'),
        
        // Controls
        playBtn: document.getElementById('play-btn'),
        pauseBtn: document.getElementById('pause-btn'),
        stopBtn: document.getElementById('stop-btn'),
        fullscreenBtn: document.getElementById('fullscreen-btn'),
        favBtn: document.getElementById('fav-btn'),
        
        // Playlists
        activePlaylist: document.getElementById('active-playlist'),
        playlistsContainer: document.getElementById('playlists-container'),
        loadBtns: document.querySelectorAll('.load-btn'),
        
        // Modal
        addPlaylistBtn: document.getElementById('add-playlist-btn'),
        addPlaylistModalBtn: document.getElementById('add-playlist-modal-btn'),
        loadDefaultBtn: document.getElementById('load-default-btn'),
        modal: document.getElementById('add-playlist-modal'),
        closeModal: document.getElementById('close-modal'),
        cancelModal: document.getElementById('cancel-modal'),
        savePlaylist: document.getElementById('save-playlist'),
        playlistUrl: document.getElementById('playlist-url'),
        playlistFile: document.getElementById('playlist-file'),
        playlistName: document.getElementById('playlist-name'),
        fileUpload: document.getElementById('file-upload'),
        fileName: document.getElementById('file-name'),
        
        // Loading
        loadingOverlay: document.getElementById('loading-overlay'),
        
        // Queue
        queueList: document.getElementById('queue-list')
    };

    // Initialize
    init();

    function init() {
        setupEventListeners();
        loadLocalPlaylists();
        updateFavoritesView();
        showView('home');
    }

    function setupEventListeners() {
        // Navigation
        elements.navBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                showView(view);
            });
        });

        // Mobile menu toggle
        elements.menuToggle?.addEventListener('click', () => {
            elements.sidebar.classList.toggle('visible');
        });

        // Search
        elements.searchInput?.addEventListener('input', debounce(handleSearch, 300));
        elements.globalSearch?.addEventListener('input', debounce(handleGlobalSearch, 300));

        // Player controls
        elements.closePlayer?.addEventListener('click', closePlayer);
        elements.playBtn?.addEventListener('click', playCurrentChannel);
        elements.pauseBtn?.addEventListener('click', pausePlayer);
        elements.stopBtn?.addEventListener('click', stopPlayer);
        elements.fullscreenBtn?.addEventListener('click', toggleFullscreen);
        elements.favBtn?.addEventListener('click', toggleFavorite);

        // Video player events
        elements.videoPlayer?.addEventListener('play', () => {
            elements.playBtn.style.display = 'none';
            elements.pauseBtn.style.display = 'flex';
        });

        elements.videoPlayer?.addEventListener('pause', () => {
            elements.playBtn.style.display = 'flex';
            elements.pauseBtn.style.display = 'none';
        });

        // Playlist loading
        elements.loadBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const url = btn.dataset.url;
                loadPlaylist(url);
            });
        });

        // Modal
        elements.addPlaylistBtn?.addEventListener('click', openModal);
        elements.addPlaylistModalBtn?.addEventListener('click', openModal);
        elements.closeModal?.addEventListener('click', closeModalHandler);
        elements.cancelModal?.addEventListener('click', closeModalHandler);
        elements.savePlaylist?.addEventListener('click', saveNewPlaylist);

        // File upload
        elements.fileUpload?.addEventListener('click', () => {
            elements.playlistFile.click();
        });

        elements.playlistFile?.addEventListener('change', handleFileSelect);

        // Drag and drop
        elements.fileUpload?.addEventListener('dragover', (e) => {
            e.preventDefault();
            elements.fileUpload.classList.add('dragover');
        });

        elements.fileUpload?.addEventListener('dragleave', () => {
            elements.fileUpload.classList.remove('dragover');
        });

        elements.fileUpload?.addEventListener('drop', (e) => {
            e.preventDefault();
            elements.fileUpload.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) {
                handleFile(file);
            }
        });

        // Load default playlist
        elements.loadDefaultBtn?.addEventListener('click', () => {
            loadPlaylist('/static/iptv_list.m3u8');
        });

        // Active playlist selector
        elements.activePlaylist?.addEventListener('change', (e) => {
            const url = e.target.value;
            if (url) {
                loadPlaylist(url);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;
            
            switch (e.key) {
                case ' ':
                    e.preventDefault();
                    togglePlayPause();
                    break;
                case 'f':
                    toggleFullscreen();
                    break;
                case 'Escape':
                    closePlayer();
                    break;
            }
        });
    }

    // View Management
    function showView(viewName) {
        state.currentView = viewName;
        
        // Update navigation
        elements.navBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === viewName);
        });

        // Update views
        elements.views.forEach(view => {
            view.classList.toggle('active', view.id === `${viewName}-view`);
        });

        // Update page title
        const titles = {
            home: 'Enigma TV',
            playlists: 'Listas de Reproducción',
            favorites: 'Mis Favoritos',
            search: 'Buscar'
        };
        elements.pageTitle.textContent = titles[viewName] || 'Enigma TV';

        // Close mobile sidebar
        elements.sidebar.classList.remove('visible');

        // Show search view specific elements
        if (viewName === 'search') {
            elements.globalSearch?.focus();
        }
    }

    // Playlist Management
    async function loadPlaylist(url) {
        showLoading(true);
        
        try {
            const response = await fetch('/api/playlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                throw new Error('Error al cargar la playlist');
            }

            const data = await response.json();
            state.channels = data.channels || [];
            state.activePlaylistUrl = url;

            updateChannelsView();
            updatePlaylistDropdown();
            showView('home');
            
        } catch (error) {
            console.error('Error loading playlist:', error);
            alert('Error al cargar la playlist: ' + error.message);
        } finally {
            showLoading(false);
        }
    }

    function loadLocalPlaylists() {
        const playlists = [
            { name: 'Lista Local', url: '/static/iptv_list.m3u8' },
            { name: 'Deportes Activos', url: '/static/deportes_activos_clean.m3u8' },
            { name: 'Mundial 2026', url: '/static/mundial2026.m3u8' },
            { name: 'Chile Activos', url: '/static/chile_activos.m3u8' },
            { name: 'Deportes Gratuitos', url: '/static/deportes_gratuitos.m3u8' },
            { name: 'Fox Sports TS', url: '/static/fox_sports_ts.m3u8' },
            { name: 'Favoritos', url: '/static/favoritos.m3u8' }
        ];

        state.playlists = playlists;
        
        // Update dropdown
        elements.activePlaylist.innerHTML = '<option value="">Seleccionar lista...</option>';
        playlists.forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist.url;
            option.textContent = playlist.name;
            elements.activePlaylist.appendChild(option);
        });
    }

    function updatePlaylistDropdown() {
        const options = elements.activePlaylist.options;
        for (let i = 0; i < options.length; i++) {
            if (options[i].value === state.activePlaylistUrl) {
                elements.activePlaylist.selectedIndex = i;
                break;
            }
        }
    }

    function loadDefaultPlaylists() {
        const defaultPlaylists = [
            '/static/iptv_list.m3u8',
            '/static/deportes_activos_clean.m3u8',
            '/static/mundial2026.m3u8',
            '/static/chile_activos.m3u8'
        ];

        defaultPlaylists.forEach(url => {
            loadPlaylist(url);
        });
    }

    // Channel Management
    function updateChannelsView() {
        const channelsHTML = createChannelsHTML(state.channels);
        elements.homeChannels.innerHTML = channelsHTML || createNoChannelsHTML();
        
        // Add event listeners to channel cards
        setupChannelCardListeners();
    }

    function createChannelsHTML(channels) {
        if (!channels || channels.length === 0) {
            return createNoChannelsHTML();
        }

        return channels.map(channel => `
            <div class="channel-card" data-url="${escapeHtml(channel.url)}" data-name="${escapeHtml(channel.name)}">
                <div class="channel-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                </div>
                <div class="channel-info">
                    <div class="channel-name">${escapeHtml(channel.name)}</div>
                    <div class="channel-group">${escapeHtml(channel.group || 'Sin categoría')}</div>
                </div>
                <div class="channel-actions">
                    <button class="channel-action-btn fav-btn ${isFavorite(channel.url) ? 'favorited' : ''}" 
                            data-url="${escapeHtml(channel.url)}" 
                            data-name="${escapeHtml(channel.name)}"
                            title="Agregar a favoritos">
                        <svg viewBox="0 0 24 24" fill="${isFavorite(channel.url) ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                        </svg>
                    </button>
                    <button class="channel-action-btn queue-btn" 
                            data-url="${escapeHtml(channel.url)}" 
                            data-name="${escapeHtml(channel.name)}"
                            title="Agregar a la cola">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');
    }

    function createNoChannelsHTML() {
        return `
            <div class="no-channels">
                <p>No hay canales cargados</p>
                <p>Selecciona o agrega una lista de reproducción</p>
            </div>
        `;
    }

    function setupChannelCardListeners() {
        // Channel click to play
        document.querySelectorAll('.channel-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.channel-action-btn')) return;
                
                const url = card.dataset.url;
                const name = card.dataset.name;
                playChannel(url, name);
            });
        });

        // Favorite buttons
        document.querySelectorAll('.fav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const url = btn.dataset.url;
                const name = btn.dataset.name;
                toggleFavoriteForChannel(url, name);
            });
        });

        // Queue buttons
        document.querySelectorAll('.queue-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const url = btn.dataset.url;
                const name = btn.dataset.name;
                addToQueue(url, name);
            });
        });
    }

    // Player Functions
    function playChannel(url, name) {
        state.currentChannel = { url, name };
        
        // Update player UI
        elements.currentChannelName.textContent = name;
        elements.currentChannelUrl.textContent = url;
        
        // Show player sidebar
        elements.playerSidebar.classList.remove('hidden');
        elements.playerSidebar.classList.add('visible');
        
        // Set video source
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

        const isHls = /\.m3u8(\?|$)/i.test(url) || /mpegurl/i.test(url);

        if (hlsInstance) {
            hlsInstance.destroy();
            hlsInstance = null;
        }

        if (isHls && window.Hls && Hls.isSupported()) {
            hlsInstance = new Hls({ lowLatencyMode: true, enableWorker: true });
            hlsInstance.loadSource(playUrl);
            hlsInstance.attachMedia(elements.videoPlayer);
            hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
                elements.videoPlayer.play().catch(error => {
                    console.error('Error playing video:', error);
                });
            });
            hlsInstance.on(Hls.Events.ERROR, (_, d) => {
                if (d.fatal) {
                    console.error('Fatal HLS error:', d.details);
                }
            });
        } else {
            elements.videoPlayer.src = playUrl;
            elements.videoPlayer.load();
            elements.videoPlayer.play().catch(error => {
                console.error('Error playing video:', error);
            });
        }

        // Update favorite button
        updateFavButton();
        
        // Highlight current channel
        document.querySelectorAll('.channel-card').forEach(card => {
            card.classList.toggle('playing', card.dataset.url === url);
        });
    }

    function playCurrentChannel() {
        if (state.currentChannel) {
            playChannel(state.currentChannel.url, state.currentChannel.name);
        }
    }

    function pausePlayer() {
        elements.videoPlayer.pause();
    }

    function stopPlayer() {
        if (hlsInstance) {
            hlsInstance.destroy();
            hlsInstance = null;
        }
        elements.videoPlayer.pause();
        elements.videoPlayer.currentTime = 0;
        elements.videoPlayer.src = '';
    }

    function togglePlayPause() {
        if (elements.videoPlayer.paused) {
            elements.videoPlayer.play();
        } else {
            elements.videoPlayer.pause();
        }
    }

    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            elements.videoPlayer.requestFullscreen().catch(err => {
                console.error('Error attempting to enable full-screen mode:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    function closePlayer() {
        elements.playerSidebar.classList.remove('visible');
        stopPlayer();
        state.currentChannel = null;
        
        document.querySelectorAll('.channel-card').forEach(card => {
            card.classList.remove('playing');
        });
    }

    // Favorites Management
    function isFavorite(url) {
        return state.favorites.some(fav => fav.url === url);
    }

    function toggleFavorite() {
        if (state.currentChannel) {
            toggleFavoriteForChannel(state.currentChannel.url, state.currentChannel.name);
        }
    }

    function toggleFavoriteForChannel(url, name) {
        const index = state.favorites.findIndex(fav => fav.url === url);
        
        if (index === -1) {
            state.favorites.push({ url, name });
        } else {
            state.favorites.splice(index, 1);
        }
        
        localStorage.setItem('enigma_favorites', JSON.stringify(state.favorites));
        updateFavButton();
        updateFavoritesView();
        updateChannelsView();
    }

    function updateFavButton() {
        if (state.currentChannel) {
            const isFav = isFavorite(state.currentChannel.url);
            elements.favBtn.classList.toggle('active', isFav);
            elements.favBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="${isFav ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
            `;
        }
    }

    function updateFavoritesView() {
        const favoritesHTML = createChannelsHTML(state.favorites);
        elements.favoritesChannels.innerHTML = favoritesHTML || `
            <div class="no-channels">
                <p>No hay canales en favoritos</p>
                <p>Agrega canales haciendo clic en el ícono de corazón</p>
            </div>
        `;
        setupChannelCardListeners();
    }

    // Queue Management
    function addToQueue(url, name) {
        state.queue.push({ url, name });
        updateQueueView();
    }

    function updateQueueView() {
        if (state.queue.length === 0) {
            elements.queueList.innerHTML = '<p class="empty-queue">No hay canales en la cola</p>';
            return;
        }

        elements.queueList.innerHTML = state.queue.map((item, index) => `
            <div class="queue-item" data-index="${index}">
                <div class="queue-item-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                </div>
                <div class="queue-item-name">${escapeHtml(item.name)}</div>
            </div>
        `).join('');

        // Add click listeners
        document.querySelectorAll('.queue-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                const queueItem = state.queue[index];
                playChannel(queueItem.url, queueItem.name);
                state.queue.splice(index, 1);
                updateQueueView();
            });
        });
    }

    // Search Functions
    function handleSearch(e) {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            updateChannelsView();
            return;
        }

        const filtered = state.channels.filter(channel => 
            channel.name.toLowerCase().includes(query) ||
            (channel.group && channel.group.toLowerCase().includes(query))
        );

        elements.homeChannels.innerHTML = createChannelsHTML(filtered);
        setupChannelCardListeners();
    }

    function handleGlobalSearch(e) {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            elements.searchResults.innerHTML = createNoChannelsHTML();
            return;
        }

        const results = state.channels.filter(channel => 
            channel.name.toLowerCase().includes(query) ||
            (channel.group && channel.group.toLowerCase().includes(query))
        );

        elements.searchResults.innerHTML = createChannelsHTML(results) || `
            <div class="no-channels">
                <p>No se encontraron resultados para "${escapeHtml(query)}"</p>
            </div>
        `;
        setupChannelCardListeners();
    }

    // Modal Functions
    function openModal() {
        elements.modal.classList.add('active');
    }

    function closeModalHandler() {
        elements.modal.classList.remove('active');
        clearModalForm();
    }

    function clearModalForm() {
        elements.playlistUrl.value = '';
        elements.playlistFile.value = '';
        elements.playlistName.value = '';
        elements.fileName.textContent = '';
    }

    async function saveNewPlaylist() {
        const url = elements.playlistUrl.value.trim();
        const name = elements.playlistName.value.trim() || 'Nueva Lista';
        
        if (!url && !elements.playlistFile.files[0]) {
            alert('Por favor ingresa una URL o selecciona un archivo');
            return;
        }

        showLoading(true);
        
        try {
            if (url) {
                await loadPlaylist(url);
            } else {
                const file = elements.playlistFile.files[0];
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/playlist/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('Error al subir el archivo');
                }

                const data = await response.json();
                state.channels = data.channels || [];
                updateChannelsView();
            }
            
            closeModalHandler();
            showView('home');
            
        } catch (error) {
            console.error('Error saving playlist:', error);
            alert('Error al guardar la playlist: ' + error.message);
        } finally {
            showLoading(false);
        }
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    }

    function handleFile(file) {
        elements.fileName.textContent = file.name;
        
        // Read file content
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            // Parse M3U content
            const channels = parseM3U(content);
            state.channels = channels;
            updateChannelsView();
        };
        reader.readAsText(file);
    }

    function parseM3U(content) {
        const channels = [];
        const lines = content.split('\n');
        
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].startsWith('#EXTINF:')) {
                const match = lines[i].match(/#EXTINF:-?\d+\s+(.*?)(?:,|\n)(.*)/);
                if (match) {
                    const group = match[1].match(/group-title="([^"]*)"/);
                    const name = match[2].trim();
                    const url = lines[i + 1]?.trim();
                    
                    if (url && !url.startsWith('#')) {
                        channels.push({
                            name: name || 'Canal sin nombre',
                            url: url,
                            group: group ? group[1] : 'Sin categoría'
                        });
                    }
                }
            }
        }
        
        return channels;
    }

    // Utility Functions
    function showLoading(show) {
        elements.loadingOverlay.classList.toggle('active', show);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});