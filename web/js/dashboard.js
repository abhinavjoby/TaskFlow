// Nav Glow Effect
const nav = document.getElementById('topNav');
const glow = document.getElementById('navGlow');

if (nav && glow) {
    nav.addEventListener('mousemove', (e) => {
        const rect = nav.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        glow.style.left = `${x}px`;
        glow.style.top = `${y}px`;
    });
}

// View Switching
function switchView(viewName) {
    document.querySelectorAll('.view-panel').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-tabs .tab').forEach(el => el.classList.remove('active'));

    const viewEl = document.getElementById(viewName + 'View');
    if (viewEl) viewEl.classList.add('active');

    const tabEl = document.querySelector(`.nav-tabs .tab[onclick="switchView('${viewName}')"]`);
    if (tabEl) tabEl.classList.add('active');

    if (viewName === 'search') {
        document.body.classList.add('hide-sidebar');
    } else {
        document.body.classList.remove('hide-sidebar');
    }

    localStorage.setItem('activeView', viewName);
}

// Ensure restored view on load
window.addEventListener('DOMContentLoaded', () => {
    let savedView = localStorage.getItem('activeView');
    if (savedView && savedView !== 'home') {
        switchView(savedView);
    }
});

// Realtime Clock
function updateClock() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'pm' : 'am';
    hours = hours % 12 || 12;

    const timeEl = document.getElementById('clockTime');
    if (timeEl) {
        timeEl.innerText = `${hours}:${minutes}`;
        document.getElementById('clockAmPm').innerText = ampm;

        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        document.getElementById('clockDate').innerHTML = `<span class="sfMed">${days[now.getDay()]} ${now.getDate()} ${months[now.getMonth()]}</span>`;
    }
}
setInterval(updateClock, 1000);
updateClock();

const pillColors = ['#ee5252', '#e09c1c', '#1dc8b7', '#4AC9FF', '#795ef3', '#e7458e', '#2fcc8e', '#8ed51b'];
function getCategoryColor(catName) {
    if (!catName) return pillColors[0];
    let hash = 0;
    for (let i = 0; i < catName.length; i++) hash += catName.charCodeAt(i);
    return pillColors[hash % pillColors.length];
}

function renderTaskCardDetailed(id, title, deadlineRaw, duration, diff, subject, status, isHighPriority = false) {
    const color = getCategoryColor(subject);
    let priorityTag = isHighPriority ? `<span style="color:#e53935; font-size:0.7rem; font-weight:bold; margin-right:5px;">🔥 high</span>` : '';
    const deadline = new Date(deadlineRaw).toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    // Only show overdue if backend explicitly says so
    let statusTag = '';
    if (status === "Overdue") statusTag = `<div style="background:#ee5252; color:#fff; border-radius:15px; padding:4px 10px; font-size:0.8rem; position:static; display:inline-block;">overdue</div>`;
    else if (status === "Ongoing") statusTag = `<div style="background:#ffcc00; color:#000; border-radius:15px; padding:4px 10px; font-size:0.8rem; position:static; display:inline-block;">ongoing</div>`;

    return `
    <div class="glass-task-card" style="display:flex; flex-direction:column; gap:8px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="display:flex; align-items:center; gap:5px;">
                <div style="background:${color}; color:#fff; border-radius:15px; padding:4px 10px; font-size:0.8rem; position:static; display:inline-block;">${subject}</div>
                ${statusTag}
            </div>
            ${priorityTag}
        </div>
        <div class="task-title sfMed" style="font-size: 1.5rem;">${title}</div>
        <div class="task-stats sfReg" style="display:flex; gap:15px; margin-top:5px; padding-top:10px; border-top: 1px solid rgba(255,255,255,0.1);">
            <div style="display:flex; flex-direction:column;">
                <span style="font-size:0.7rem; opacity:0.6;">deadline</span>
                <span>${deadline}</span>
            </div>
            <div style="display:flex; flex-direction:column;">
                <span style="font-size:0.7rem; opacity:0.6;">difficulty</span>
                <span>${diff}</span>
            </div>
            <div style="display:flex; flex-direction:column;">
                <span style="font-size:0.7rem; opacity:0.6;">duration</span>
                <span>${duration}</span>
            </div>
        </div>
        <div style="display:flex; gap: 10px; margin-top:10px; justify-content:flex-end">
            <button class="start-focus-btn sfMed" style="border-radius:20px; padding:10px 20px; flex: 1;" onclick="startFocusFromTask('${title}', '${subject}', ${parseInt(duration)}, '${id}')">start focus</button>
            <button class="sfMed" style="border-radius:20px; padding: 1px 13px; background: rgba(31, 136, 255, 1); color: #ffffffff; border:none" onclick="markTaskDone('${id}')">✓</button>
        </div>
    </div>`;
}

function renderTaskCardCarousel(id, title, deadline, duration, diff, subject) {
    const color = getCategoryColor(subject);
    return `
    <div class="glass-task-card search-card" style="display:flex; flex-direction:column; justify-content:space-between;">
        <div>
            <div style="background:${color}; color:#fff; border-radius:15px; padding:4px 10px; font-size:0.8rem; display:inline-block; position:static;">${subject}</div>
            <div class="task-card-header" style="margin-top:10px;">
                <div class="task-title sfMed" style="font-size: 1.4rem;">${title}</div>
            </div>
        </div>
        <div class="task-stats sfReg" style="margin-top:auto; border-top: 1px solid rgba(255,255,255,0.1); padding-top:15px; display:flex; gap:15px; align-items:center;">
            <div style="display:flex; flex-direction:column;"><span style="font-size:0.7rem; opacity:0.6;">deadline</span><span>${deadline}</span></div>
            <div style="display:flex; flex-direction:column; flex:1;"><span style="font-size:0.7rem; opacity:0.6;">duration</span><span>${duration}</span></div>
            <button onclick="startFocusFromTask('${title}', '${subject}', parseInt('${duration}'), '${id}')" style="align-self: flex-end; width: 35px; height: 35px; border-radius: 50%; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255,255,255,0.2); color: var(--textPrimary); font-size: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">▶</button>
        </div>
    </div>`;
}

function renderTaskCardCalendar(id, title, deadline, subject, dayIndex, hour, min, duration) {
    const color = getCategoryColor(subject);
    // Removed exact top offset to allow stacking without overlap
    return `<div class="glass-task-card" style="grid-column: ${dayIndex + 1}; height: fit-content; margin-bottom: 10px; font-size: 0.9rem; padding:15px; display:flex; flex-direction:column; gap:10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border:none;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div class="sfMed" style="background:${color}; color:#fff; border-radius:10px; padding:3px 10px; display:inline-block; position:static;">${subject}</div>
                </div>
                <div class="sfMed" style="font-size:1.1rem;">${title}</div>
                <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                    <div class="sfReg" style="color:var(--textSecondary); font-size: 0.8rem;">${deadline}</div>
                    <button onclick="startFocusFromTask('${title}', '${subject}', ${duration}, '${id}')" style="width: 30px; height: 30px; border-radius: 50%; background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255,255,255,0.2); color: var(--textPrimary); font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">▶</button>
                </div>
            </div>`;
}

// Initial Empty States
const emptyStateHTML = `<div class="sfMed" style="text-align:center; padding:30px; color:var(--textSecondary)">no tasks scheduled</div>`;
if (document.getElementById('todayTaskList')) {
    document.getElementById('todayTaskList').innerHTML = emptyStateHTML;
    document.getElementById('urgentTaskList').innerHTML = emptyStateHTML;
    document.getElementById('searchCarousel').innerHTML = '';
}

// Populate Calendar Header
function renderCalendarHeader() {
    const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    let html = '';
    for (let i = 0; i < 7; i++) {
        let d = new Date();
        d.setDate(d.getDate() + i);
        html += `<div class="cal-col-header"><div class="cal-day">${days[d.getDay()]}</div><div class="cal-date">${d.getDate()}</div></div>`;
    }
    document.getElementById('calHeader').innerHTML = html;
}
renderCalendarHeader();

let _cachedCategories = [];
let _cachedProjects = [];
let _activeCategoryContext = { focus: '', task: '', goal: '', project: '' }; // Currently selected pill

async function loadUserData() {
    if (window.eel) {
        const profile = await eel.get_user_profile()();
        if (profile && profile.username) {
            document.getElementById('greetingText').innerText = `Hi, ${profile.username || 'User'}!`;
            const profileDisplay = document.getElementById('profileUsername');
            if (profileDisplay) profileDisplay.innerText = profile.username;

            // Set initial energy slider
            const currentEnergy = profile.energy || 2;
            const slider = document.getElementById('energySlider');
            if (slider) {
                slider.value = currentEnergy;
                updateEnergyLabel(currentEnergy);
            }

            _cachedCategories = profile.categories || [];
            renderFilterPillsUI();
        }

        try {
            _cachedProjects = await eel.get_all_projects()();
        } catch (e) { _cachedProjects = []; }

        const emptyStateHTML = `<div class="sfMed" style="text-align:center; padding:30px; color:var(--textSecondary); display: flex; justify-content: center; width: 100%;">No tasks found</div>`;

        // Urgent Tasks Update
        const currentEnergy = profile && profile.energy ? profile.energy : 2;
        const urgentData = await eel.get_urgent_tasks(10, currentEnergy)();
        window._urgentTasksData = urgentData && urgentData.tasks ? urgentData.tasks : [];
        renderUrgentTasks();

        // Load dashboard stats
        try {
            const statsData = await eel.get_focus_stats('all')();
            if (statsData && statsData.all_time_summary) {
                document.getElementById('dashStatActivity').innerHTML = `${statsData.all_time_summary.total_hours}<span class="sym">h</span>`;
                document.getElementById('dashStatFocus').innerHTML = `${statsData.all_time_summary.avg_focus_score}<span class="sym">%</span>`;
                document.getElementById('dashStatDone').innerHTML = `${statsData.all_time_summary.completion_pct}<span class="sym">%</span>`;
            }
        } catch (e) {
            console.error("Failed to load dashboard stats", e);
        }

        // All Tasks Update (Search & Today)
        const allTasks = await eel.get_all_tasks()();
        window._allTasksData = allTasks; // Cache for search filtering

        if (allTasks && allTasks.length > 0) {
            const todayHtml = allTasks.filter(t => {
                const td = new Date(t.deadline);
                const now = new Date();
                return td.toDateString() === now.toDateString();
            }).map(t =>
                renderTaskCardDetailed(t.id, t.title, t.deadline, `${t.duration}min`, t.difficulty, t.subject, t.status, false)
            ).join('');

            const carouselHtml = allTasks.map(t =>
                renderTaskCardCarousel(t.id, t.title, new Date(t.deadline).toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }), `${t.duration}min`, t.difficulty, t.subject)
            ).join('');

            document.getElementById('todayTaskList').innerHTML = todayHtml || emptyStateHTML;
            document.getElementById('searchCarousel').innerHTML = carouselHtml;

            // Build Calendar Plot
            let calHtml = '';
            const now = new Date();
            now.setHours(0, 0, 0, 0);

            const endOfWeek = new Date(now);
            endOfWeek.setDate(now.getDate() + 7);

            allTasks.forEach(t => {
                const tDateObj = new Date(t.deadline);
                const tDateOnly = new Date(tDateObj);
                tDateOnly.setHours(0, 0, 0, 0);

                if (tDateOnly >= now && tDateOnly < endOfWeek) {
                    const diffDays = Math.round((tDateOnly - now) / 86400000);
                    const hr = tDateObj.getHours();
                    const min = tDateObj.getMinutes();
                    calHtml += renderTaskCardCalendar(t.id, t.title, tDateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), t.subject, diffDays, hr, min, t.duration);
                }
            });
            document.getElementById('calGrid').innerHTML = calHtml;
        } else {
            document.getElementById('todayTaskList').innerHTML = emptyStateHTML;
            document.getElementById('searchCarousel').innerHTML = emptyStateHTML;
            document.getElementById('calGrid').innerHTML = emptyStateHTML;
        }

        // Goals Update
        const allGoals = await checkGoalsWrapper();
        if (allGoals && allGoals.length > 0) {
            // Filter out boolean goals completed more than 24 hours ago
            const activeGoals = allGoals.filter(g => {
                if (g.metric_type === 'BOOLEAN' && g.current_value) {
                    if (g.last_updated) {
                        const hrsSince = (new Date() - new Date(g.last_updated)) / 36e5;
                        return hrsSince < 24;
                    }
                }
                return true;
            });
            document.getElementById('goalsList').innerHTML = activeGoals.map(g => {
                const isDone = g.metric_type === 'BOOLEAN' ? g.current_value : g.current_value >= g.target_value;
                const innerVal = g.metric_type !== 'BOOLEAN' ? `<span style="font-size: 0.8rem; font-weight:bold; color: ${isDone ? '#fff' : 'var(--textSecondary)'};">${g.current_value}</span>` : '';
                return `
                <div class="goal-item sfReg" style="display:flex; justify-content:space-between; align-items:center;">
                    <div><span>${g.title}</span></div>
                    <div class="goal-radio ${isDone ? 'done' : ''}" style="cursor:pointer; display:flex; justify-content:center; align-items:center;" onclick="incrementGoalFront('${g.id}')">${innerVal}</div>
                </div>`;
            }).join('');
        } else {
            document.getElementById('goalsList').innerHTML = emptyStateHTML;
        }

        // Immediately render focus popup's dropdown to have categories ready
        renderFocusCategories();
    }
}

window._pillsExpanded = false;

function renderFilterPillsUI() {
    if (!window._cachedCategories) return;
    
    let filterHtml = '';
    const maxVisible = 4;
    const isExpanded = window._pillsExpanded;
    const catsToShow = isExpanded ? window._cachedCategories : window._cachedCategories.slice(0, maxVisible);
    
    catsToShow.forEach(c => {
        const color = getCategoryColor(c);
        const isSelected = window.currentUrgentFilter === c;
        // Make selected pill solid, non-selected semi-transparent
        filterHtml += `<button class="filter-pill sfMed" style="background:${color}; color:#fff; ${isSelected ? 'border: 2px solid var(--textPrimary); transform: scale(1.05); opacity: 1;' : 'opacity: 0.5;'}" onclick="applyFilter('${c}')">${c}</button>`;
    });
    
    if (window._cachedCategories.length > maxVisible) {
        if (!isExpanded) {
            filterHtml += `<button class="filter-pill sfMed" style="background:rgba(255,255,255,0.2); color:var(--textPrimary); border:1px solid rgba(255,255,255,0.2);" onclick="toggleFilterPills(true)">▾</button>`;
        } else {
            filterHtml += `<button class="filter-pill sfMed" style="background:rgba(255,255,255,0.2); color:var(--textPrimary); border:1px solid rgba(255,255,255,0.2);" onclick="toggleFilterPills(false)">▴</button>`;
        }
    }
    
    document.getElementById('filterPills').innerHTML = filterHtml;
}

function toggleFilterPills(expand) {
    window._pillsExpanded = expand;
    renderFilterPillsUI();
}

window.currentUrgentFilter = null;
function applyFilter(cat) {
    if (window.currentUrgentFilter === cat) {
        window.currentUrgentFilter = null; // Toggle off
    } else {
        window.currentUrgentFilter = cat;
    }

    renderFilterPillsUI();

    renderUrgentTasks();
}

function renderUrgentTasks() {
    const emptyStateHTML = `<div class="sfMed" style="text-align:center; padding:30px; color:var(--textSecondary); display: flex; justify-content: center; width: 100%;">No tasks found</div>`;
    if (window._urgentTasksData && window._urgentTasksData.length > 0) {
        let filtered = window._urgentTasksData;
        if (window.currentUrgentFilter) {
            filtered = filtered.filter(t => t.subject === window.currentUrgentFilter);
        }

        if (filtered.length > 0) {
            document.getElementById('urgentTaskList').innerHTML = filtered.map((t, idx) =>
                renderTaskCardDetailed(t.id, t.title, t.deadline, `${t.duration}min`, t.difficulty, t.subject, t.status, idx === 0)
            ).join('');
        } else {
            document.getElementById('urgentTaskList').innerHTML = emptyStateHTML;
        }
    } else {
        document.getElementById('urgentTaskList').innerHTML = emptyStateHTML;
    }
}

async function checkGoalsWrapper() {
    if (window.eel && window.eel.get_all_goals) {
        return await eel.get_all_goals()();
    }
    return [];
}

async function markTaskDone(id) {
    if (window.eel) {
        await eel.update_task_status(id, 'Completed')();
        loadUserData();
    }
}

async function incrementGoalFront(id) {
    if (window.eel) {
        await eel.increment_goal(id)();
        loadUserData();
    }
}

const searchInput = document.querySelector('.glass-search');
if (searchInput) {
    searchInput.addEventListener('input', function (e) {
        const term = e.target.value.toLowerCase().trim();
        if (!window._allTasksData) window._allTasksData = [];

        const carousel = document.getElementById('searchCarousel');
        if (!term) {
            carousel.innerHTML = window._allTasksData.map(t =>
                renderTaskCardCarousel(t.id, t.title, new Date(t.deadline).toLocaleString(), `${t.duration}min`, t.difficulty, t.subject)
            ).join('');
            return;
        }

        const filtered = window._allTasksData.filter(t =>
            (t.title || '').toLowerCase().includes(term) || (t.subject || '').toLowerCase().includes(term)
        );

        if (filtered.length > 0) {
            carousel.innerHTML = filtered.map(t =>
                renderTaskCardCarousel(t.id, t.title, new Date(t.deadline).toLocaleString(), `${t.duration}min`, t.difficulty, t.subject)
            ).join('');
        } else {
            carousel.innerHTML = `<div class="sfMed" style="text-align:center; padding:30px; color:var(--textSecondary); width:100%;">no matches found</div>`;
        }
    });
}

window.addEventListener('load', () => {
    setTimeout(() => {
        if (document.getElementById('todayTaskList')) {
            loadUserData();
        }
    }, 200);
});

// Generate Category HTML Component for regular forms
function generateCategoryPills(contextKey) {
    let html = `<div class="filter-pills" style="margin-bottom:0; display:flex; align-items:center;">`;
    _cachedCategories.forEach((cat, idx) => {
        let isSelected = _activeCategoryContext[contextKey] === cat;
        const color = getCategoryColor(cat);
        html += `<button type="button" class="filter-pill sfMed" style="background:${color}; color:#fff; ${isSelected ? 'border: 2px solid var(--textPrimary); opacity: 1; transform:scale(1.05);' : 'opacity: 0.6;'}" onclick="selectCategory('${contextKey}', '${cat}')">${cat}</button>`;
    });
    html += `<span class="pill-add-btn sfMed" id="pillAddBtn_${contextKey}" onclick="showCategoryInput('${contextKey}')">+</span>`;
    html += `<input type="text" id="pillInput_${contextKey}" class="cat-input-mini sfReg" style="display:none;" placeholder="New" onkeydown="handleCategoryEnter(event, '${contextKey}')" onblur="hideCategoryInput('${contextKey}')">`;
    html += `</div>`;
    return html;
}

function selectCategory(contextKey, cat) {
    _activeCategoryContext[contextKey] = cat;
    const space = document.getElementById(`${contextKey}CategorySpace`);
    if (space) space.innerHTML = generateCategoryPills(contextKey);
}

function showCategoryInput(contextKey) {
    document.getElementById(`pillAddBtn_${contextKey}`).style.display = 'none';
    const input = document.getElementById(`pillInput_${contextKey}`);
    input.style.display = 'inline-block';
    input.focus();
}

function hideCategoryInput(contextKey) {
    document.getElementById(`pillAddBtn_${contextKey}`).style.display = 'inline-flex';
    document.getElementById(`pillInput_${contextKey}`).style.display = 'none';
}

async function handleCategoryEnter(e, contextKey) {
    if (e.key === 'Enter') {
        const val = e.target.value.trim();
        if (val && !_cachedCategories.includes(val)) {
            _cachedCategories.push(val);
            if (window.eel) {
                _cachedCategories = await eel.add_category(val)();
            }
        }
        selectCategory(contextKey, val); // auto-select newly made one
    }
}

// Generate the Dropdown specifically for focus view as requested
function renderFocusCategories() {
    const space = document.getElementById('focusCategorySpace');
    if (!space) return;

    let html = `<select id="focusCategory" class="glass-input sfReg" onchange="handleFocusSelectChange(this)">`;
    html += `<option value="" disabled selected>Select Category</option>`;
    _cachedCategories.forEach(cat => {
        html += `<option value="${cat}">${cat}</option>`;
    });
    html += `<option value="__NEW__">+ Create New</option>`;
    html += `</select>`;

    // Hidden Input for actual typing overlay
    html += `<input type="text" id="focusCategoryNew" class="glass-input sfReg" style="display:none; margin-top:5px;" placeholder="Type new and press Enter" onkeydown="handleFocusCatEnter(event)" onblur="hideFocusCatInput()">`;

    space.innerHTML = html;
}

function handleFocusSelectChange(selectEl) {
    if (selectEl.value === '__NEW__') {
        selectEl.style.display = 'none';
        const input = document.getElementById('focusCategoryNew');
        input.style.display = 'block';
        input.focus();
    }
}

function togglePopup(id) {
    const el = document.getElementById(id);
    if (el) {
        el.style.display = (el.style.display === 'block') ? 'none' : 'block';
    }
}

function updateEnergyLabel(val) {
    const label = document.getElementById('energyLabel');
    const slider = document.getElementById('energySlider');
    if (!label || !slider) return;
    val = parseInt(val);
    if (val === 1) {
        label.innerText = "Low";
        label.style.color = "var(--pillColor1)"; // Red
        slider.style.accentColor = "var(--pillColor1)";
    } else if (val === 2) {
        label.innerText = "Med";
        label.style.color = "var(--pillColor2)"; // Yellow
        slider.style.accentColor = "var(--pillColor2)";
    } else if (val === 3) {
        label.innerText = "High";
        label.style.color = "var(--pillColor7)"; // Green
        slider.style.accentColor = "var(--pillColor7)";
    }
}

async function updateEnergyLevel(val) {
    if (window.eel) {
        await eel.update_user_energy(parseInt(val))();
        loadUserData(); // Reload to refresh urgent tasks sorting based on new energy
    }
}

function hideFocusCatInput() {
    const txt = document.getElementById('focusCategoryNew');
    if (!txt.value) {
        txt.style.display = 'none';
        document.getElementById('focusCategory').style.display = 'block';
        document.getElementById('focusCategory').value = '';
    }
}

async function handleFocusCatEnter(e) {
    if (e.key === 'Enter') {
        const val = e.target.value.trim();
        if (val && !_cachedCategories.includes(val)) {
            _cachedCategories.push(val);
            if (window.eel) {
                _cachedCategories = await eel.add_category(val)();
            }
        }
        renderFocusCategories();
        document.getElementById('focusCategory').value = val;
    }
}


// Add Popup Tab Switcher - Completely DOM Injected!
function switchAddTab(tabName) {
    document.querySelectorAll('.add-tab').forEach(el => {
        el.style.opacity = '0.6';
        el.style.fontWeight = 'normal';
    });
    const target = document.getElementById('add-tab-' + tabName);
    if (target) {
        target.style.opacity = '1';
        target.style.fontWeight = 'bold';
    }

    const container = document.getElementById('addPopupContent');
    _activeCategoryContext[tabName] = _cachedCategories[0] || '';

    if (tabName === 'task') {
        let projOptions = '<option value="">None</option>';
        if (_cachedProjects && _cachedProjects.length > 0) {
            _cachedProjects.forEach(p => {
                projOptions += `<option value="${p.id}">${p.name}</option>`;
            });
        }

        container.innerHTML = `
            <div id="addTaskForm" class="add-form-view">
                <div style="margin-bottom: 15px;">
                    <span class="popup-lbl sfReg">name</span>
                    <input type="text" id="addNameTask" class="glass-input sfReg" required>
                </div>
                <div style="margin-bottom: 15px; display:flex; flex-direction:column;">
                    <span class="popup-lbl sfReg" style="margin-bottom: 4px;">category</span>
                    <div id="taskCategorySpace" style="width: 100%;">
                        ${generateCategoryPills('task')}
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <div>
                            <span class="popup-lbl sfReg">time required (min)</span>
                            <input type="number" id="addTimeReqTask" class="glass-input sfReg" placeholder="e.g. 120" style="height:45px; padding: 10px; font-size:0.8rem;" required>
                        </div>
                        <div>
                            <span class="popup-lbl sfReg">deadline</span>
                            <input type="datetime-local" id="addDeadlineTask" class="glass-input sfReg" style="height:45px; padding: 10px; font-size:0.8rem;" required>
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <span class="popup-lbl sfReg">description</span>
                    <textarea id="addDescTask" class="glass-input sfReg" style="resize:none; height:45px;"></textarea>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; align-items: center;">
                    <div>
                        <span class="popup-lbl sfReg">link to project</span>
                        <select id="addProjTask" class="glass-input sfReg">
                            ${projOptions}
                        </select>
                    </div>
                    <div>
                        <span class="popup-lbl sfReg" style="margin-bottom: 10px;">difficulty</span>
                        <div style="display:flex; align-items:center; gap: 10px;">
                            <span class="sfReg" style="color:var(--textSecondary)">1</span>
                            <input type="range" id="addDiffTask" min="1" max="5" value="3" class="custom-slider" style="flex:1;">
                            <span class="sfReg" style="color:var(--textSecondary)">5</span>
                        </div>
                    </div>
                </div>
                <div style="display:flex; justify-content:flex-end;">
                    <button class="btn-blue sfMed" onclick="submitAddForm('task')" style="padding: 10px 30px; border-radius: 30px;">save task</button>
                </div>
            </div>
        `;
    } else if (tabName === 'goal') {
        container.innerHTML = `
            <div id="addGoalForm" class="add-form-view">
                <div style="margin-bottom: 15px;">
                    <span class="popup-lbl sfReg">title</span>
                    <input type="text" id="addNameGoal" class="glass-input sfReg" required>
                </div>
                <div style="margin-bottom: 15px; display:flex; flex-direction:column;">
                    <span class="popup-lbl sfReg" style="margin-bottom: 4px;">category</span>
                    <div id="goalCategorySpace" style="width: 100%;">
                        ${generateCategoryPills('goal')}
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 15px;">
                    <div>
                        <span class="popup-lbl sfReg">metric type</span>
                        <select id="addMetricGoal" class="glass-input sfReg">
                            <option value="COUNT">Count</option>
                            <option value="DURATION">Duration</option>
                            <option value="BOOLEAN">Boolean</option>
                        </select>
                    </div>
                    <div>
                        <span class="popup-lbl sfReg">target value</span>
                        <input type="number" id="addTargetGoal" class="glass-input sfReg" placeholder="e.g., 5" required>
                    </div>
                </div>
                <div style="margin-bottom: 25px;">
                    <span class="popup-lbl sfReg">reset period</span>
                    <select id="addResetGoal" class="glass-input sfReg">
                        <option value="Daily">Daily</option>
                        <option value="Weekly">Weekly</option>
                        <option value="Monthly">Monthly</option>
                        <option value="Never">Never</option>
                    </select>
                </div>
                <div style="display:flex; justify-content:flex-end;">
                    <button class="btn-blue sfMed" onclick="submitAddForm('goal')" style="padding: 10px 30px; border-radius: 30px;">save goal</button>
                </div>
            </div>
        `;
    } else if (tabName === 'project') {
        container.innerHTML = `
            <div id="addProjectForm" class="add-form-view">
                <div style="margin-bottom: 15px;">
                    <span class="popup-lbl sfReg">name</span>
                    <input type="text" id="addNameProject" class="glass-input sfReg" required>
                </div>
                <div style="margin-bottom: 15px; display:flex; flex-direction:column;">
                    <span class="popup-lbl sfReg" style="margin-bottom: 4px;">subject</span>
                    <div id="projectCategorySpace" style="width: 100%;">
                        ${generateCategoryPills('project')}
                    </div>
                </div>
                <div style="margin-bottom: 25px;">
                    <span class="popup-lbl sfReg">overall notes</span>
                    <textarea id="addNotesProject" class="glass-input sfReg" style="resize:none; height:100px;"></textarea>
                </div>
                <div style="display:flex; justify-content:flex-end;">
                    <button class="btn-blue sfMed" onclick="submitAddForm('project')" style="padding: 10px 30px; border-radius: 30px;">save project</button>
                </div>
            </div>
        `;
    }
}

// Form Handlers
async function startFocusSession() {
    const name = document.getElementById('focusName').value.trim();
    const category = document.getElementById('focusCategory').value;
    const duration = document.getElementById('focusDuration').value;

    if (!name || !category || !duration) {
        alert("Please fill out all Focus Mode fields.");
        return;
    }

    // Redirect to standalone Focus Mode
    window.location.href = `focus.html?title=${encodeURIComponent(name)}&subject=${encodeURIComponent(category)}&duration=${duration}`;
}

function startFocusFromTask(title, subject, duration, taskId) {
    window.location.href = `focus.html?title=${encodeURIComponent(title)}&subject=${encodeURIComponent(subject)}&duration=${duration}&taskId=${taskId || ''}`;
}

async function submitAddForm(type) {
    if (type === 'task') {
        const name = document.getElementById('addNameTask').value.trim();
        const cat = _activeCategoryContext['task'];
        const durationMins = document.getElementById('addTimeReqTask').value;
        const deadline = document.getElementById('addDeadlineTask').value;

        if (!name || !cat || !durationMins || !deadline) {
            alert("Name, Category, Time Required, and Deadline are required for Tasks.");
            return;
        }

        const d2 = new Date(deadline);

        const payload = {
            title: name,
            subject: cat,
            difficulty: parseInt(document.getElementById('addDiffTask').value),
            energy_req: 2,
            deadline: d2.toISOString(),
            duration: parseInt(durationMins),
            notes: [document.getElementById('addDescTask').value],
            parent_refs: [document.getElementById('addProjTask').value]
        };

        if (window.eel) await eel.add_task(payload)();

    } else if (type === 'goal') {
        const title = document.getElementById('addNameGoal').value.trim();
        const cat = _activeCategoryContext['goal'];
        const tVal = document.getElementById('addTargetGoal').value;

        if (!title || !cat || !tVal) {
            alert("Title, Category, and Target Value are required for Goals.");
            return;
        }

        const payload = {
            title: title,
            category: cat,
            metric_type: document.getElementById('addMetricGoal').value,
            target_value: parseInt(tVal) || parseInt(tVal) !== 0,
            current_value: 0,
            reset_period: document.getElementById('addResetGoal').value
        };

        if (window.eel) await eel.add_goal(payload)();

    } else if (type === 'project') {
        const name = document.getElementById('addNameProject').value.trim();
        const subj = _activeCategoryContext['project'];

        if (!name || !subj) {
            alert("Name and Subject are required for Projects.");
            return;
        }

        const payload = {
            name: name,
            subject: subj,
            overall_notes: document.getElementById('addNotesProject').value
        };

        if (window.eel) await eel.add_project(payload)();
    }

    togglePopup('addPopup');
    loadUserData();
}
