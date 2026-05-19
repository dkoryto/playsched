// static/js/app.js

function t(key, fallback) {
    const dict = window.I18N || {};
    return dict[key] !== undefined ? dict[key] : (fallback !== undefined ? fallback : key);
}

function showToast(message, type = 'success', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

document.addEventListener('DOMContentLoaded', () => {
    // --- Global Variables ---
    let allPlaylists = [];
    let filteredPlaylists = [];
    let currentDisplayPage = 1;
    const PLAYLIST_DISPLAY_LIMIT = 25;
    let searchTimeout = null;
    let currentDevices = [];

    // --- DOM Elements ---
    const loginButton = document.getElementById('login-button');
    const logoutButton = document.getElementById('logout-button');
    const mainAppDiv = document.getElementById('main-app');
    const playlistListUl = document.getElementById('playlist-list');
    const scheduleListUl = document.getElementById('schedule-list');
    const refreshPlaylistsBtn = document.getElementById('refresh-playlists');
    const refreshSchedulesBtn = document.getElementById('refresh-schedules');
    const exportSchedulesBtn = document.getElementById('export-schedules-button');
    const importSchedulesBtn = document.getElementById('import-schedules-button');
    const importSchedulesFile = document.getElementById('import-schedules-file');
    const scheduleFormContainer = document.getElementById('schedule-form-container');
    const scheduleForm = document.getElementById('schedule-form');
    const formTitle = document.getElementById('form-title');
    const formPlaylistName = document.getElementById('form-playlist-name');
    const formPlaylistUri = document.getElementById('form-playlist-uri');
    const formInputPlaylistUri = document.getElementById('form-input-playlist-uri');
    const formInputPlaylistName = document.getElementById('form-input-playlist-name');
    const formDeviceSelect = document.getElementById('form-device');
    const formStartTime = document.getElementById('form-start-time');
    const formStopTime = document.getElementById('form-stop-time');
    const formVolume = document.getElementById('form-volume');
    const formTimezone = document.getElementById('form-timezone');
    const formScheduleId = document.getElementById('schedule-id');
    const cancelScheduleButton = document.getElementById('cancel-schedule-button');
    const playNowFormButton = document.getElementById('play-now-form-button');
    const testDeviceButton = document.getElementById('test-device-button');
    const selectAllDaysBtn = document.getElementById('select-all-days');
    const selectNoDaysBtn = document.getElementById('select-no-days');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const playlistSearchInput = document.getElementById('playlist-search');
    const playlistPaginationDiv = document.getElementById('playlist-pagination');
    const playlistPrevBtn = document.getElementById('playlist-prev');
    const playlistNextBtn = document.getElementById('playlist-next');
    const playlistPageInfo = document.getElementById('playlist-page-info');

    // Now Playing controls
    const npBtnPrev = document.getElementById('np-btn-prev');
    const npBtnPlay = document.getElementById('np-btn-play');
    const npBtnPause = document.getElementById('np-btn-pause');
    const npBtnStop = document.getElementById('np-btn-stop');
    const npBtnNext = document.getElementById('np-btn-next');
    const npBtnMute = document.getElementById('np-btn-mute');

    // --- Initialization ---
    function init() {
        console.log("App initializing...");
        initTheme();
        initLang();
        initClock();
        if (mainAppDiv) {
            setupEventListeners();
            loadPlaylists();
            loadSchedules();
            loadDevices();
            initNowPlaying();
        } else if (loginButton) {
            loginButton.addEventListener('click', () => {
                window.location.href = '/login';
            });
        }
    }

    // --- Language Toggle ---
    function initLang() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', () => switchLanguage(btn.dataset.lang));
        });
    }

    async function switchLanguage(newLang) {
        if (!newLang || newLang === window.LANG) return;
        try {
            const response = await fetch('/api/set_language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lang: newLang }),
            });
            if (response.ok) {
                window.location.reload();
            } else {
                console.error('Failed to set language');
            }
        } catch (e) {
            console.error('Error setting language:', e);
        }
    }

    // --- Theme Toggle ---
    function initTheme() {
        const savedTheme = localStorage.getItem('playsched-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            document.body.classList.add('dark-mode');
            updateThemeButton(true);
        }
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }
    }

    function toggleTheme() {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('playsched-theme', isDark ? 'dark' : 'light');
        updateThemeButton(isDark);
    }

    function updateThemeButton(isDark) {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.textContent = isDark ? '☀️' : '🌙';
            themeToggle.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
        }
    }

    // --- Live Clock ---
    function initClock() {
        const clockEl = document.getElementById('live-clock');
        if (!clockEl) return;

        function updateClock() {
            const now = new Date();
            const dateStr = now.toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
            const timeStr = now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            clockEl.textContent = `${dateStr}  ${timeStr}`;
        }

        updateClock();
        setInterval(updateClock, 1000);
    }

    // --- Event Listeners Setup ---
    function setupEventListeners() {
        if (logoutButton) logoutButton.addEventListener('click', () => window.location.href = '/logout');
        const panelLogoutBtn = document.getElementById('panel-logout-button');
        if (panelLogoutBtn) panelLogoutBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/panel_logout', {method: 'POST'});
            } catch (e) {}
            window.location.reload();
        });
        if (refreshPlaylistsBtn) refreshPlaylistsBtn.addEventListener('click', loadPlaylists);
        if (refreshSchedulesBtn) refreshSchedulesBtn.addEventListener('click', loadSchedules);
        if (exportSchedulesBtn) exportSchedulesBtn.addEventListener('click', handleExportSchedules);
        if (importSchedulesBtn) importSchedulesBtn.addEventListener('click', () => importSchedulesFile?.click());
        if (importSchedulesFile) importSchedulesFile.addEventListener('change', handleImportSchedules);
        if (playlistSearchInput) playlistSearchInput.addEventListener('input', handlePlaylistFilterInput);
        if (scheduleForm) scheduleForm.addEventListener('submit', handleSaveSchedule);
        if (cancelScheduleButton) cancelScheduleButton.addEventListener('click', hideScheduleForm);
        if (playNowFormButton) playNowFormButton.addEventListener('click', handlePlayNowFromForm);
        if (testDeviceButton) testDeviceButton.addEventListener('click', handleTestDevice);
        if (selectAllDaysBtn) selectAllDaysBtn.addEventListener('click', () => toggleAllDays(true));
        if (selectNoDaysBtn) selectNoDaysBtn.addEventListener('click', () => toggleAllDays(false));

        // Tab switching
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTabId = button.getAttribute('data-tab');
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                button.classList.add('active');
                document.getElementById(targetTabId).classList.add('active');
            });
        });

        // Event delegation for dynamically added buttons in lists
        if (playlistListUl) playlistListUl.addEventListener('click', handlePlaylistClick);
        if (scheduleListUl) scheduleListUl.addEventListener('click', handleScheduleActionClick);

        // Pagination buttons
        if (playlistPrevBtn) playlistPrevBtn.addEventListener('click', () => changeDisplayPage(-1));
        if (playlistNextBtn) playlistNextBtn.addEventListener('click', () => changeDisplayPage(1));

        // Now Playing controls
        if (npBtnPrev) npBtnPrev.addEventListener('click', () => handleNpControl('previous'));
        if (npBtnPlay) npBtnPlay.addEventListener('click', () => handleNpControl('play'));
        if (npBtnPause) npBtnPause.addEventListener('click', () => handleNpControl('pause'));
        if (npBtnStop) npBtnStop.addEventListener('click', () => handleNpControl('pause'));
        if (npBtnNext) npBtnNext.addEventListener('click', () => handleNpControl('next'));
        if (npBtnMute) npBtnMute.addEventListener('click', handleNpMuteToggle);
    }

    // --- API Call Functions ---
    async function fetchData(url, options = {}) {
        if (!options.headers) {
             options.headers = {};
        }
        if (options.body && typeof options.body === 'string' && !options.headers['Content-Type']) {
             options.headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(url, options);
            if (response.status === 401) {
                console.error("API Error 401: Unauthorized. Session likely expired.");
                alert(t('error_session_expired'));
                window.location.href = '/logout';
                return null;
            }
            if (!response.ok) {
                let errorData = { error: `HTTP error ${response.status}` };
                try { errorData = await response.json(); } catch (e) { errorData.error = errorData.error + `: ${response.statusText}`; }
                console.error(`API Error (${url}): ${response.status}`, errorData);
                alert(`Error: ${errorData.error || `Failed to fetch data from ${url}`}`);
                return null;
            }
            if (response.status === 204) { return { success: true }; }
            return await response.json();
        } catch (error) {
            console.error(`Network/Fetch Error (${url}):`, error);
            alert(t('error_network'));
            return null;
        }
    }


    // --- Data Loading Functions ---
    async function loadPlaylists() {
        console.log("Loading ALL playlists from backend...");
        playlistListUl.innerHTML = `<li>${t('loading_playlists')}</li>`;
        playlistPaginationDiv.style.display = 'none';
        playlistSearchInput.value = '';

        const url = `/api/playlists`;
        const data = await fetchData(url);

        if (data) {
            allPlaylists = data;
            console.log(`Loaded ${allPlaylists.length} playlists total.`);
            filterAndDisplayPlaylists();
        } else {
            allPlaylists = [];
            filteredPlaylists = [];
            playlistListUl.innerHTML = `<li>${t('failed_to_load', 'Failed to load playlists.')}</li>`;
            renderPaginationControls();
        }
    }

    async function loadDevices() {
        console.log("Loading devices...");
        const devices = await fetchData('/api/devices');
        currentDevices = devices || [];
        renderDeviceOptions(currentDevices);
    }

     async function loadSchedules() {
        console.log("Loading schedules...");
        scheduleListUl.innerHTML = `<li>${t('loading_schedules')}</li>`;
        const schedules = await fetchData('/api/schedules');
        renderSchedules(schedules || []);
    }

    // --- Filtering and Display Logic ---

    function filterAndDisplayPlaylists() {
        const searchTerm = playlistSearchInput.value.toLowerCase().trim();

        if (searchTerm) {
            filteredPlaylists = allPlaylists.filter(playlist =>
                playlist.name.toLowerCase().includes(searchTerm)
            );
        } else {
            filteredPlaylists = [...allPlaylists];
        }

        renderPaginatedView();
    }

    function renderPaginatedView() {
        const startIndex = (currentDisplayPage - 1) * PLAYLIST_DISPLAY_LIMIT;
        const endIndex = startIndex + PLAYLIST_DISPLAY_LIMIT;
        const playlistsToShow = filteredPlaylists.slice(startIndex, endIndex);

        renderPlaylistSlice(playlistsToShow);
        renderPaginationControls();
    }

    function renderPlaylistSlice(playlistsSlice) {
        playlistListUl.innerHTML = '';
        if (!playlistsSlice || playlistsSlice.length === 0) {
            playlistListUl.innerHTML = '';
            const li = document.createElement('li');
            const searchTerm = playlistSearchInput.value.trim();
            li.textContent = searchTerm
                ? t('no_playlists_matching', 'No playlists found matching "{term}".').replace('{term}', searchTerm)
                : t('no_playlists', 'No playlists found.');
            playlistListUl.appendChild(li);
            return;
        }
        playlistsSlice.forEach(p => {
            const li = document.createElement('li');
            const safeName = p.name.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const safeUri = p.uri.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const safeAttrName = p.name.replace(/"/g, '&quot;').replace(/</g, "&lt;").replace(/>/g, "&gt;");
            li.innerHTML = `${safeName} <button class="add-schedule-btn" data-uri="${safeUri}" data-name="${safeAttrName}">${t('schedule', 'Schedule')}</button>`;
            playlistListUl.appendChild(li);
        });
    }

    function renderPaginationControls() {
        if (!playlistPaginationDiv) return;

        const totalFilteredItems = filteredPlaylists.length;
        const totalPages = Math.ceil(totalFilteredItems / PLAYLIST_DISPLAY_LIMIT);

        if (totalPages <= 1) {
            playlistPaginationDiv.style.display = 'none';
            return;
        }

        playlistPaginationDiv.style.display = 'flex';
        playlistPageInfo.textContent = `${t('loading')} Page ${currentDisplayPage} of ${totalPages} (${totalFilteredItems} ${t('loading')})`;
        // Keep simple English page info since it's mostly numeric
        playlistPageInfo.textContent = `Page ${currentDisplayPage} of ${totalPages} (${totalFilteredItems})`;
        playlistPrevBtn.disabled = (currentDisplayPage <= 1);
        playlistNextBtn.disabled = (currentDisplayPage >= totalPages);

        playlistPaginationDiv.dataset.totalPages = totalPages;
    }

    function renderDeviceOptions(devices) {
        formDeviceSelect.innerHTML = `<option value="">${t('select_device', '-- Select Device --')}</option>`;
        if (!devices || devices.length === 0) {
            formDeviceSelect.innerHTML += `<option value="" disabled>${t('no_active_devices', 'No active devices found')}</option>`;
            return;
        }
        devices.forEach(d => {
            const option = document.createElement('option');
            option.value = d.id;
            option.textContent = `${d.name.replace(/</g, "&lt;").replace(/>/g, "&gt;")} (${d.type})`;
            if (d.is_active) {
                 option.textContent += " ★ Active";
                 option.style.fontWeight = 'bold';
            }
            formDeviceSelect.appendChild(option);
        });
    }

    function renderSchedules(schedules) {
        scheduleListUl.innerHTML = '';
       if (!schedules || schedules.length === 0) {
           scheduleListUl.innerHTML = `<li style="animation: fadeInUp 0.4s ease;">${t('no_schedules')}</li>`;
           return;
       }

       schedules.forEach(s => {
           const li = document.createElement('li');
           const daysStr = s.days_of_week ? getDaysString(s.days_of_week) : (s.play_once_triggered ? t('played_once') : t('play_once'));
           const stopStr = s.stop_time_local ? ` - ${s.stop_time_local}` : "";
           const volumeStr = s.volume !== null ? ` | ${t('vol')}: ${s.volume}%` : "";
           const statusStr = s.is_active ? t('active') : t('paused');
           const toggleBtnText = s.is_active ? t('toggle_pause', 'Pause') : t('toggle_unpause', 'Unpause');
           const statusClassName = s.is_active ? "status-active" : "status-paused";
           const safePlaylistName = (s.playlist_name || 'Unknown Playlist').replace(/</g, "&lt;").replace(/>/g, "&gt;");
           const safeDeviceName = (s.target_device_name || s.target_device_id || 'Unknown Device').replace(/</g, "&lt;").replace(/>/g, "&gt;");

           let nextRunStr = "N/A";
           const nextTimeUTC_ISO = s._next_play_time_utc_iso;

           if (nextTimeUTC_ISO) {
               try {
                   const nextDate = new Date(nextTimeUTC_ISO);
                   const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: 'numeric' };
                   nextRunStr = nextDate.toLocaleString(undefined, options);
               } catch (e) {
                   console.error("Error parsing next run date:", nextTimeUTC_ISO, e);
                   nextRunStr = "Error parsing date";
               }
           } else if (!s.is_active) {
               nextRunStr = t('paused');
           } else if (s.play_once_triggered) {
                nextRunStr = t('played_once');
           }

           const shuffleStr = s.shuffle_state ? t('on') : t('off');
           li.innerHTML = `
                <div class="schedule-header">
                    <strong>${safePlaylistName}</strong>
                    <span class="schedule-device">${t('device')} ${safeDeviceName}</span>
                </div>
                <div class="schedule-details">
                    <span>${t('time')}: ${s.start_time_local}${stopStr} (${s.timezone || '?'})</span>
                    <span>${t('days')}: ${daysStr}</span>
                    ${volumeStr ? `<span>${t('vol')}: ${s.volume}%</span>` : ''}
                    <span>${t('shuffle_short')}: ${shuffleStr}</span>
                </div>
                <div class="schedule-status-line">
                    <span class="schedule-info-label">${t('next_run')}:</span> <span class="schedule-next-run">${nextRunStr}</span>
                </div>
                 <div class="schedule-status-line">
                    <span class="schedule-info-label">${t('status')}:</span> <span class="schedule-status ${statusClassName}">${statusStr}</span>
                 </div>
                <div class="schedule-actions">
                    <button class="move-up-btn" data-id="${s.id}" title="Move up">⬆️</button>
                    <button class="move-down-btn" data-id="${s.id}" title="Move down">⬇️</button>
                    <button class="play-now-btn" data-id="${s.id}" title="${t('play_now')}">${t('play_now')}</button>
                    <button class="stop-now-btn" data-id="${s.id}" title="${t('stop')}">${t('stop')}</button>
                    <button class="toggle-active-btn" data-id="${s.id}" title="${toggleBtnText}">${toggleBtnText}</button>
                    <button class="edit-schedule-btn" data-id="${s.id}" title="${t('edit')}">${t('edit')}</button>
                    <button class="duplicate-schedule-btn" data-id="${s.id}" title="${t('duplicate')}">${t('duplicate')}</button>
                    <button class="delete-schedule-btn" data-id="${s.id}" title="${t('delete')}">${t('delete')}</button>
                </div>
           `;
           li.dataset.scheduleData = JSON.stringify(s);
           scheduleListUl.appendChild(li);
       });
   }

    // --- Event Handlers ---
     function changeDisplayPage(direction) {
         const totalFilteredItems = filteredPlaylists.length;
         const totalPages = Math.ceil(totalFilteredItems / PLAYLIST_DISPLAY_LIMIT);
         const nextPage = currentDisplayPage + direction;

         if (nextPage >= 1 && nextPage <= totalPages) {
             currentDisplayPage = nextPage;
             renderPaginatedView();
         } else {
             console.log("Boundary hit, page not changed.");
         }
    }

    function handlePlaylistFilterInput() {
         clearTimeout(searchTimeout);
         searchTimeout = setTimeout(() => {
             currentDisplayPage = 1;
             filterAndDisplayPlaylists();
         }, 300);
    }

    function handlePlaylistClick(event) {
        if (event.target.classList.contains('add-schedule-btn')) {
            const button = event.target;
            const uri = button.getAttribute('data-uri');
            const name = button.getAttribute('data-name');
            openScheduleForm({ playlist_uri: uri, playlist_name: name });
        }
    }

     async function handleScheduleActionClick(event) {
         const button = event.target.closest('button');
         console.log('Schedule action click:', button?.className, button?.textContent);
         if (!button) return;

         const scheduleId = button.getAttribute('data-id');
         if (!scheduleId) return;

         if (button.classList.contains('move-up-btn') || button.classList.contains('move-down-btn')) {
             const direction = button.classList.contains('move-up-btn') ? 'up' : 'down';
             const result = await fetchData(`/api/schedules/${scheduleId}/move`, { method: 'PUT', body: JSON.stringify({direction}) });
             if (result) loadSchedules();
         } else if (button.classList.contains('play-now-btn')) {
             console.log(`Playing schedule ${scheduleId} now...`);
             button.textContent = t('playing', 'Playing...'); button.disabled = true;
             const result = await fetchData(`/api/schedules/${scheduleId}/play_now`, { method: 'POST' });
             if (result) { setTimeout(() => { showToast(result.message || t('toast_playback_initiated'), "success"); button.textContent = t('play_now'); button.disabled = false; }, 500); }
             else { button.textContent = t('play_now'); button.disabled = false; }
         } else if (button.classList.contains('stop-now-btn')) {
             console.log(`Stopping schedule ${scheduleId} now...`);
             button.textContent = t('stopping', 'Stopping...'); button.disabled = true;
             const result = await fetchData(`/api/schedules/${scheduleId}/stop_now`, { method: 'POST' });
             if (result) { setTimeout(() => { showToast(result.message || t('toast_playback_stopped'), "info"); button.textContent = t('stop'); button.disabled = false; }, 500); }
             else { button.textContent = t('stop'); button.disabled = false; }
         } else if (button.classList.contains('toggle-active-btn')) {
              console.log(`Toggling schedule ${scheduleId}...`);
             const result = await fetchData(`/api/schedules/${scheduleId}/toggle`, { method: 'PUT' });
             if (result) loadSchedules();
         } else if (button.classList.contains('edit-schedule-btn')) {
              console.log(`Editing schedule ${scheduleId}...`);
             const scheduleData = JSON.parse(button.closest('li').dataset.scheduleData || '{}');
             openScheduleForm(scheduleData);
            } else if (button.classList.contains('duplicate-schedule-btn')) {
                console.log(`Duplicating schedule ${scheduleId}...`);
                const listItem = button.closest('li');
                if (listItem && listItem.dataset.scheduleData) {
                    try {
                        const scheduleData = JSON.parse(listItem.dataset.scheduleData);
                        const duplicatedData = { ...scheduleData };
                        delete duplicatedData.id;
                        delete duplicatedData.last_triggered_utc;
                        delete duplicatedData.play_once_triggered;
                        delete duplicatedData._next_play_time_utc_iso;
                        delete duplicatedData._sort_obj;
                        openScheduleForm(duplicatedData);
                    } catch (e) {
                        console.error("Error parsing schedule data for duplication:", e);
                        alert("Error: Could not read schedule data for duplication.");
                    }
                } else {
                     console.error(`Could not find schedule data for ID ${scheduleId} to duplicate.`);
                     alert("Error: Could not find schedule data to duplicate.");
                }
         } else if (button.classList.contains('delete-schedule-btn')) {
             if (confirm(t('confirm_delete_schedule'))) {
                 console.log(`Deleting schedule ${scheduleId}...`);
                  const result = await fetchData(`/api/schedules/${scheduleId}`, { method: 'DELETE' });
                 if (result) { console.log("Delete successful", result); loadSchedules(); }
                 else { console.log("Delete failed"); }
             }
         }
    }

    async function handleSaveSchedule(event) {
        event.preventDefault();
        console.log("Saving schedule... button clicked, form data:");

        const scheduleId = formScheduleId.value;
        const isEditing = !!scheduleId;

        const selectedDays = Array.from(document.querySelectorAll('#schedule-form input[id^="day-"]:checked')).map(cb => cb.value);
        const daysOfWeekStr = selectedDays.join(',');
        const targetDeviceId = formDeviceSelect.value;
        const targetDeviceName = formDeviceSelect.options[formDeviceSelect.selectedIndex]?.text.split(' (')[0];
        const startTime = formStartTime.value;
        const timezone = formTimezone.value || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';

        if (!targetDeviceId) { alert(t('select_device')); return; }
        if (!startTime) { alert(t('start_time')); return; }
        if (!timezone) { alert(t('timezone')); return; }
        if (!daysOfWeekStr && !isEditing) {
             if (!confirm(t('confirm_no_days'))) { return; }
        }
        const shuffleState = document.getElementById('form-shuffle').checked;

        const scheduleData = {
            playlist_uri: formInputPlaylistUri.value,
            playlist_name: formInputPlaylistName.value,
            target_device_id: targetDeviceId,
            target_device_name: targetDeviceName,
            days_of_week: daysOfWeekStr,
            start_time_local: startTime,
            stop_time_local: formStopTime.value || null,
            volume: formVolume.value ? parseInt(formVolume.value, 10) : null,
            timezone: timezone,
            shuffle_state: shuffleState,
        };
         if (isEditing) {
             const originalData = JSON.parse(document.querySelector(`li[data-schedule-data*='"id":${scheduleId}']`)?.dataset.scheduleData || '{}');
             scheduleData.is_active = originalData?.is_active ?? 1;
             if((daysOfWeekStr && !originalData?.days_of_week) || (!daysOfWeekStr && originalData?.days_of_week)) {
                  scheduleData.play_once_triggered = 0;
             }
         }

        console.log("Data to save:", scheduleData);
        const url = isEditing ? `/api/schedules/${scheduleId}` : '/api/schedules';
        const method = isEditing ? 'PUT' : 'POST';

        const result = await fetchData(url, { method: method, body: JSON.stringify(scheduleData) });
        if (result && !result.error) {
            console.log("Save successful:", result);
            hideScheduleForm(); loadSchedules();
        } else { console.error("Failed to save schedule."); }
    }

     function handlePlayNowFromForm() {
         const playlistUri = formInputPlaylistUri.value;
         const deviceId = formDeviceSelect.value;
         const volume = formVolume.value ? parseInt(formVolume.value, 10) : null;

         if (!playlistUri || !deviceId) { alert(t('select_device')); return; }

         console.log(`Playing playlist ${playlistUri} on device ${deviceId} now...`);
         playNowFormButton.textContent = t('playing'); playNowFormButton.disabled = true;

         fetchData('/api/play_now', { method: 'POST', body: JSON.stringify({ playlist_uri: playlistUri, device_id: deviceId, volume: volume }) })
         .then(result => {
              if (result) { setTimeout(() => { showToast(result.message || t('toast_playback_initiated'), "success"); playNowFormButton.textContent = t('play_now'); playNowFormButton.disabled = false; }, 500); }
              else { playNowFormButton.textContent = t('play_now'); playNowFormButton.disabled = false; }
         });
    }

    async function handleNpControl(action) {
        const url = `/api/playback/${action}`;
        const result = await fetchData(url, { method: 'POST' });
        if (result) {
            let toastKey = 'toast_playback_initiated';
            if (action === 'pause') toastKey = 'toast_playback_paused';
            if (action === 'play') toastKey = 'toast_playback_resumed';
            if (action === 'next') toastKey = 'toast_next_track';
            if (action === 'previous') toastKey = 'toast_prev_track';
            showToast(result.message || t(toastKey), 'success');
            setTimeout(updateNowPlaying, 800);
        }
    }

    let lastVolumeBeforeMute = null;

    function updateNpPlayPauseButtons(isPlaying) {
        if (!npBtnPlay || !npBtnPause) return;
        if (isPlaying) {
            npBtnPlay.style.display = 'none';
            npBtnPause.style.display = 'inline-flex';
        } else {
            npBtnPlay.style.display = 'inline-flex';
            npBtnPause.style.display = 'none';
        }
    }

    async function handleNpMuteToggle() {
        if (!npBtnMute) return;
        const isMuted = npBtnMute.dataset.muted === '1';
        let targetVolume;
        if (isMuted) {
            targetVolume = lastVolumeBeforeMute !== null ? lastVolumeBeforeMute : 50;
        } else {
            const currentState = await fetchData('/api/current_playback');
            lastVolumeBeforeMute = currentState && currentState.track ? (currentState.track.volume_percent || 50) : 50;
            targetVolume = 0;
        }
        const result = await fetchData('/api/playback/volume', { method: 'POST', body: JSON.stringify({volume: targetVolume}) });
        if (result) {
            if (isMuted) {
                npBtnMute.dataset.muted = '0';
                npBtnMute.textContent = '🔊';
                npBtnMute.title = 'Mute';
            } else {
                npBtnMute.dataset.muted = '1';
                npBtnMute.textContent = '🔇';
                npBtnMute.title = 'Unmute';
            }
            setTimeout(updateNowPlaying, 500);
        }
    }

    // --- UI Helper Functions ---
    async function handleExportSchedules() {
        const data = await fetchData('/api/schedules/export');
        if (!data) return;
        const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `playsched-backup-${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(t('toast_exported', 'Schedules exported'), 'success');
    }

    async function handleImportSchedules(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        try {
            const text = await file.text();
            const json = JSON.parse(text);
            if (!json.schedules || !Array.isArray(json.schedules)) {
                alert('Invalid file format: missing "schedules" array');
                return;
            }
            if (!confirm(`Import ${json.schedules.length} schedules?`)) return;
            const result = await fetchData('/api/schedules/import', {
                method: 'POST',
                body: JSON.stringify(json)
            });
            if (result) {
                showToast(t('toast_imported', 'Schedules imported') + `: ${result.imported}/${result.total}`, result.errors?.length ? 'warning' : 'success');
                loadSchedules();
            }
        } catch (e) {
            alert('Error reading file: ' + e.message);
        } finally {
            event.target.value = '';
        }
    }

    async function handleTestDevice() {
        const deviceId = formDeviceSelect.value;
        const playlistUri = formInputPlaylistUri.value;
        if (!deviceId) { alert(t('select_device')); return; }
        testDeviceButton.disabled = true;
        testDeviceButton.textContent = 'Testing...';
        const result = await fetchData('/api/test_device', {
            method: 'POST',
            body: JSON.stringify({ device_id: deviceId, playlist_uri: playlistUri })
        });
        if (result) {
            showToast(result.message || 'Test playback started', 'info');
        }
        testDeviceButton.disabled = false;
        testDeviceButton.textContent = '🔊 Test';
    }

    function openScheduleForm(data = {}) {
        scheduleForm.reset();
        formScheduleId.value = '';

        formPlaylistName.textContent = data.playlist_name || 'N/A';
        formPlaylistUri.textContent = data.playlist_uri || 'N/A';
        formInputPlaylistUri.value = data.playlist_uri || '';
        formInputPlaylistName.value = data.playlist_name || '';

        renderDeviceOptions(currentDevices);
        if (data.target_device_id) {
            formDeviceSelect.value = data.target_device_id;
        } else {
             formDeviceSelect.value = '';
        }

        toggleAllDays(false);
        const days = data.days_of_week ? data.days_of_week.split(',').map(d => d.trim()) : [];
        days.forEach(dayIndex => {
            try {
                const dayName = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][parseInt(dayIndex, 10)];
                if (dayName) {
                    const checkbox = document.getElementById(`day-${dayName}`);
                    if (checkbox) {
                        checkbox.checked = true;
                    } else {
                        console.warn(`Checkbox for day index ${dayIndex} (day-${dayName}) not found.`);
                    }
                }
            } catch (e) { console.error("Error parsing day index:", dayIndex, e); }
        });

        formStartTime.value = data.start_time_local || '';
        formStopTime.value = data.stop_time_local || '';
        formVolume.value = data.volume !== null ? data.volume : '';
        formTimezone.value = data.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Paris';

        const shuffleCheckbox = document.getElementById('form-shuffle');
        if (shuffleCheckbox) {
            shuffleCheckbox.checked = data.shuffle_state ? true : false;
        }

        if (data.id) {
            formTitle.textContent = t('edit_schedule');
            formScheduleId.value = data.id;
        } else if (Object.keys(data).length > 0 && data.playlist_uri) {
            formTitle.textContent = t('add_schedule_from_duplicate');
        } else {
            formTitle.textContent = t('add_schedule');
            formTimezone.value = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Paris';
        }

        scheduleFormContainer.style.display = 'block';
        scheduleFormContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function hideScheduleForm() {
        scheduleFormContainer.style.display = 'none';
        scheduleForm.reset();
        formScheduleId.value = '';
    }

     function toggleAllDays(select) {
        const checkboxes = document.querySelectorAll('#schedule-form input[id^="day-"]');
        checkboxes.forEach(cb => cb.checked = select);
    }

    function getDaysString(daysOfWeekStr) {
        if (!daysOfWeekStr) return t('play_once');
        const daysMap = [t('mon'), t('tue'), t('wed'), t('thu'), t('fri'), t('sat'), t('sun')];
        try {
            return daysOfWeekStr.split(',')
                               .map(d => parseInt(d.trim(), 10))
                               .filter(i => i >= 0 && i < 7)
                               .sort((a, b) => a - b)
                               .map(i => daysMap[i])
                               .join(', ');
        } catch (e) { return "Invalid Days"; }
    }


    // --- Now Playing Widget ---
    let nowPlayingInterval = null;
    let lastProgressMs = 0;
    let lastDurationMs = 0;
    let lastFetchTime = 0;

    function initNowPlaying() {
        updateNowPlaying();
        nowPlayingInterval = setInterval(updateNowPlaying, 5000);
        setInterval(updateProgressBar, 1000);

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (nowPlayingInterval) {
                    clearInterval(nowPlayingInterval);
                    nowPlayingInterval = null;
                }
            } else {
                updateNowPlaying();
                if (!nowPlayingInterval) {
                    nowPlayingInterval = setInterval(updateNowPlaying, 5000);
                }
            }
        });
    }

    async function updateNowPlaying() {
        try {
            const response = await fetch('/api/current_playback');
            if (!response.ok) {
                if (response.status === 401 || response.status === 503) {
                    hideNowPlaying();
                }
                return;
            }
            const data = await response.json();
            if (!data.is_playing || !data.track) {
                hideNowPlaying();
                return;
            }
            showNowPlaying(data);
        } catch (err) {
            console.error('Now playing fetch error:', err);
        }
    }

    function showNowPlaying(data) {
        const widget = document.getElementById('now-playing-widget');
        if (!widget) return;
        widget.style.display = 'flex';

        const cover = document.getElementById('np-cover');
        const title = document.getElementById('np-title');
        const artist = document.getElementById('np-artist');
        const device = document.getElementById('np-device');
        const timeEl = document.getElementById('np-time');
        const durationEl = document.getElementById('np-duration');
        const nextTitle = document.getElementById('np-next-title');
        const nextArtist = document.getElementById('np-next-artist');

        if (cover) cover.src = data.track.image || '';
        if (title) title.textContent = data.track.name;
        if (artist) artist.textContent = data.track.artists;
        if (device) device.textContent = data.device_name || '';

        lastProgressMs = data.track.progress_ms || 0;
        lastDurationMs = data.track.duration_ms || 1;
        lastFetchTime = Date.now();

        if (timeEl) timeEl.textContent = formatMs(lastProgressMs);
        if (durationEl) durationEl.textContent = formatMs(lastDurationMs);

        updateProgressBar();

        const upNextList = document.getElementById('np-up-next-list');
        if (upNextList) {
            if (data.up_next && data.up_next.length > 0) {
                upNextList.innerHTML = data.up_next.map((t, i) => `
                    <div class="np-up-next-item" style="margin-top: ${i > 0 ? '8px' : '0'}; padding-top: ${i > 0 ? '8px' : '0'}; ${i > 0 ? 'border-top: 1px solid var(--border);' : ''}">
                        <div class="np-next-title">${t.name.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
                        <div class="np-next-artist">${t.artists.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
                    </div>
                `).join('');
            } else {
                upNextList.innerHTML = '<div class="np-next-title">--</div><div class="np-next-artist">--</div>';
            }
        }

        updateNpPlayPauseButtons(data.is_playing);
    }

    function hideNowPlaying() {
        const widget = document.getElementById('now-playing-widget');
        if (widget) widget.style.display = 'none';
    }

    function updateProgressBar() {
        if (!lastDurationMs || lastDurationMs <= 0) return;
        const elapsed = Date.now() - lastFetchTime;
        const currentProgress = Math.min(lastProgressMs + elapsed, lastDurationMs);
        const pct = (currentProgress / lastDurationMs) * 100;
        const bar = document.getElementById('np-progress');
        const timeEl = document.getElementById('np-time');
        if (bar) bar.style.width = pct + '%';
        if (timeEl) timeEl.textContent = formatMs(currentProgress);
    }

    function formatMs(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return minutes + ':' + String(seconds).padStart(2, '0');
    }

    // --- Panel Login Overlay ---
    async function checkPanelAuth() {
        try {
            const response = await fetch('/api/panel_auth_status');
            const data = await response.json();
            if (data.required && !data.authenticated) {
                showPanelLoginOverlay();
                return false;
            }
            hidePanelLoginOverlay();
            init();
            return true;
        } catch (e) {
            console.error('Panel auth check failed:', e);
            init();
            return true;
        }
    }

    function showPanelLoginOverlay() {
        const overlay = document.getElementById('panel-login-overlay');
        if (overlay) overlay.style.display = 'flex';
        setupPanelLoginListeners();
    }

    function hidePanelLoginOverlay() {
        const overlay = document.getElementById('panel-login-overlay');
        if (overlay) overlay.style.display = 'none';
    }

    function setupPanelLoginListeners() {
        const btn = document.getElementById('panel-login-button');
        const input = document.getElementById('panel-password-input');
        const errorEl = document.getElementById('panel-login-error');
        if (!btn || !input) return;

        btn.addEventListener('click', async () => {
            errorEl.textContent = '';
            try {
                const resp = await fetch('/api/panel_login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password: input.value})
                });
                if (resp.ok) {
                    hidePanelLoginOverlay();
                    const mainApp = document.getElementById('main-app');
                    if (mainApp) mainApp.style.display = '';
                    const authSection = document.getElementById('auth-section');
                    if (authSection) authSection.style.display = '';
                    init();
                } else {
                    errorEl.textContent = t('panel_login_error', 'Invalid password');
                    input.value = '';
                    input.focus();
                }
            } catch (e) {
                errorEl.textContent = t('error_network');
            }
        });

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') btn.click();
        });
        input.focus();
    }

    // --- Register Service Worker (PWA) ---
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(() => console.log('Service Worker registered'))
            .catch((err) => console.log('Service Worker registration failed:', err));
    }

    // --- Start the App ---
    checkPanelAuth();

}); // End DOMContentLoaded
