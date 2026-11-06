(() => {
    'use strict';

    const $ = (id) => document.getElementById(id);
    const els = {
        connection: $('connection-state'), setup: $('setup-panel'), work: $('work-panel'),
        result: $('result-panel'), datasetName: $('dataset-name'), classes: $('defect-classes'),
        roles: $('camera-roles'), create: $('create-session'), setupMessage: $('setup-message'),
        startCell: $('start-cell'), palletInfo: $('pallet-info'), stationState: $('station-state'),
        sessionTitle: $('session-title'), sessionStatus: $('session-status'), partsCount: $('parts-count'),
        framesCount: $('frames-count'), partNumber: $('part-number'), partProgress: $('part-progress'),
        cellChip: $('cell-chip'), newPart: $('new-part'), finishPart: $('finish-part'),
        stationHome: $('station-home'), export: $('export-dataset'),
        finishSession: $('finish-session'), workflowMessage: $('workflow-message'), cameraTitle: $('camera-title'),
        cellGrid: $('cell-grid'), palletProgress: $('pallet-progress'),
        frameId: $('frame-id'), wrap: $('canvas-wrap'), emptyState: $('empty-state'), image: $('frame-image'),
        canvas: $('annotation-canvas'), frameRole: $('frame-role'), frameSize: $('frame-size'),
        annotationHelp: $('annotation-help'), palette: $('element-palette'),
        newElement: $('new-element'), addElement: $('add-element'),
        classSelect: $('defect-class'), finishPolygon: $('finish-polygon'),
        noDefect: $('no-defect'), clearBox: $('clear-box'), save: $('save-annotation'),
        nextCamera: $('next-camera'), annotationMessage: $('annotation-message'),
        resultText: $('result-text'), resultYaml: $('result-yaml'),
    };

    let config = null;
    let state = null;
    let currentFrame = null;
    let annotations = [];
    let draftPoints = [];
    let draftClass = '';
    let hoverPoint = null;
    let noDefectSelected = false;
    let lastError = '';
    let busy = false;

    function setMessage(element, text, kind = '') {
        if (!element) return;
        element.textContent = text || '';
        element.className = element.className.replace(/\b(error|ok)\b/g, '').trim();
        if (kind) element.classList.add(kind);
    }

    async function api(path, options = {}) {
        const response = await fetch(path, {
            ...options,
            headers: {'Content-Type': 'application/json', ...(options.headers || {})},
        });
        let payload = null;
        try { payload = await response.json(); } catch (_) { payload = {}; }
        if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
        return payload;
    }

    function selectedValues(container) {
        return [...container.querySelectorAll('input[type="checkbox"]:checked')]
            .map((item) => item.value);
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>'"]/g, (char) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
        }[char]));
    }

    // Названия ролей как в production-проекте (project/alghorithms/contour.py):
    // near — камера 0, far — камера 1, middle — камера 2. Индексы можно
    // переопределить ключом --indices, поэтому подпись берётся из конфигурации.
    const ROLE_TITLES = {
        near: 'Ближняя',
        far: 'Дальняя',
        middle: 'Верхняя',
    };
    let cameraMapping = {};

    function roleTitle(role) {
        const title = ROLE_TITLES[role] || role;
        const index = cameraMapping[role];
        return Number.isInteger(index) ? `${title} (камера ${index})` : title;
    }

    function fillSetup(data) {
        config = data;
        cameraMapping = data.camera_mapping || {};
        els.classes.value = data.defect_classes.join(', ');
        els.roles.replaceChildren();
        data.camera_roles.forEach((role) => {
            const label = document.createElement('label');
            label.className = 'check-item';
            label.innerHTML = `<input type="checkbox" value="${escapeHtml(role)}" checked>` +
                `<span>${escapeHtml(roleTitle(role))}</span>`;
            els.roles.appendChild(label);
        });
        els.startCell.value = String(data.start_cell || 1);
        renderPalletInfo(data.pallet);
        renderStation(data.stations || data.station || {});
    }

    function renderPalletInfo(pallet) {
        if (!pallet || pallet.error) {
            els.palletInfo.textContent = pallet && pallet.error ? pallet.error : '—';
            els.palletInfo.classList.add('error');
            return;
        }
        els.palletInfo.classList.remove('error');
        els.palletInfo.textContent = `${pallet.rows} × ${pallet.columns} = ${pallet.total} корпусов · ` +
            `шаг ${pallet.step_x} × ${pallet.step_y} мм`;
        if (pallet.start_cell && !els.startCell.dataset.touched) {
            els.startCell.value = String(pallet.start_cell);
        }
    }

    function renderStation(station) {
        if (!station) { els.stationState.textContent = '—'; return; }
        if (station.enabled === false) {
            els.stationState.textContent = 'Движение отключено (--motion off): кадры снимаются с текущей позиции';
            els.stationState.className = 'field-static';
            return;
        }
        const position = station.position;
        const pos = position
            ? `X=${position.x} Y=${position.y} Z=${position.z}`
            : 'позиция неизвестна';
        els.stationState.textContent = `${station.connected ? 'Подключена' : 'Не подключена'} · ${pos}` +
            (station.port ? ` · ${station.port}` : '');
        els.stationState.className = `field-static ${station.connected ? 'ok' : 'muted'}`;
    }

    function fillClasses(names) {
        const selected = els.classSelect.value;
        els.classSelect.replaceChildren();
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = 'Выберите элемент…';
        els.classSelect.appendChild(placeholder);
        (names || []).forEach((name) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            els.classSelect.appendChild(option);
        });
        if ([...(names || [])].includes(selected)) els.classSelect.value = selected;
        renderPalette(names || []);
    }

    function renderPalette(names) {
        if (!els.palette) return;
        els.palette.replaceChildren();
        (names || []).forEach((name) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'palette-item';
            button.dataset.element = name;
            button.textContent = name;
            button.disabled = !annotationEditable();
            button.addEventListener('click', () => selectElement(name));
            els.palette.appendChild(button);
        });
        updatePaletteSelection();
    }

    function annotationEditable() {
        return Boolean(currentFrame) && !els.save.disabled && !busy;
    }

    function selectElement(name) {
        if (draftPoints.length && name !== draftClass) {
            setMessage(els.annotationMessage, 'Сначала завершите текущую область.', 'error');
            return;
        }
        els.classSelect.value = name || '';
        noDefectSelected = false;
        els.noDefect.classList.remove('selected');
        updatePaletteSelection();
        redrawAnnotations();
    }

    function updatePaletteSelection() {
        if (!els.palette) return;
        [...els.palette.querySelectorAll('.palette-item')].forEach((button) => {
            button.classList.toggle('selected', button.dataset.element === els.classSelect.value);
            button.disabled = !annotationEditable();
        });
    }

    function renderPallet(cells, pallet) {
        if (!els.cellGrid) return;
        els.cellGrid.style.setProperty('--cols', String((pallet && pallet.columns) || 10));
        els.cellGrid.replaceChildren();
        const list = cells || [];
        list.forEach((cell) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'cell-button';
            button.textContent = String(cell.cell_id);
            if (cell.cell_id % 2 === 0) button.classList.add('alt-row');
            if (cell.collected) button.classList.add('collected');
            if (cell.current) button.classList.add('current');
            button.title = `Ячейка ${cell.cell_id} · ряд ${cell.row + 1}, колонка ${cell.column + 1}\n` +
                `X=${cell.x} Y=${cell.y} Z=${cell.z}` +
                (cell.part_id ? `\nкорпус #${cell.part_id}` : '');
            button.disabled = busy || !(state && state.active);
            button.addEventListener('click', () => moveToCell(cell.cell_id));
            els.cellGrid.appendChild(button);
        });
        const done = list.filter((cell) => cell.collected).length;
        els.palletProgress.textContent = `${done} / ${list.length}`;
    }

    function renderState(next) {
        state = next || state;
        if (!state) return;
        const session = state.session || {};
        const part = state.part;
        const expected = (state.camera_roles || []).length;
        const frameIds = part && Array.isArray(part.frame_ids) ? part.frame_ids : [];
        els.sessionTitle.textContent = session.session_id || '—';
        els.partsCount.textContent = session.part_count ?? 0;
        els.framesCount.textContent = session.frame_count ?? 0;
        els.sessionStatus.textContent = state.active ? (part ? 'СБОРКА' : 'ГОТОВА') : 'ЗАВЕРШЕНА';
        els.partNumber.textContent = part ? `#${part.part_id}` : '—';
        if (part) {
            const cell = part.cell_id ? `ячейка ${part.cell_id}` : 'ячейка без координат';
            els.partProgress.textContent = `${cell} · ${frameIds.length} из ${expected} камер снято · ` +
                (state.next_role ? `следующая: ${roleTitle(state.next_role)}` : 'все камеры готовы');
            els.cellChip.classList.remove('hidden');
            const coordinates = part.coordinates
                ? `X=${part.coordinates.x} Y=${part.coordinates.y} Z=${part.coordinates.z}`
                : 'координаты не заданы';
            els.cellChip.textContent = `ряд ${(part.row ?? 0) + 1}, колонка ${(part.column ?? 0) + 1} · ${coordinates}`;
        } else {
            els.cellChip.classList.add('hidden');
            if (state.next_cell) {
                els.partProgress.textContent = state.active
                    ? `Следующий корпус — ячейка ${state.next_cell.cell_id} ` +
                      `(ряд ${state.next_cell.row + 1}, колонка ${state.next_cell.column + 1})`
                    : 'Сессия завершена';
            } else {
                els.partProgress.textContent = state.active
                    ? 'Все ячейки паллеты сняты — завершите набор'
                    : 'Сессия завершена';
            }
        }
        const frameBusy = Boolean(currentFrame) || Boolean(state.current_frame);
        els.newPart.disabled = busy || !state.active || Boolean(part) || frameBusy || !state.next_cell;
        els.finishPart.disabled = busy || !state.active || !part || frameBusy || frameIds.length !== expected;
        els.stationHome.disabled = busy || !state.active || Boolean(part) || frameBusy;
        els.finishSession.disabled = busy || !state.active || Boolean(part) || frameBusy ||
            Number(session.frame_count || 0) === 0;
        els.export.disabled = busy || !state.active || Number(session.frame_count || 0) === 0;
        renderPallet(state.cells || [], state.pallet || {});
        renderStation(state.station);
        if (state.pallet && !state.pallet.error) renderPalletInfo(state.pallet);
        if (!currentFrame) {
            els.save.disabled = true;
            els.finishPolygon.disabled = true;
            els.noDefect.disabled = true;
            els.clearBox.disabled = true;
            els.classSelect.disabled = true;
            els.newElement.disabled = busy || !state.active;
            els.addElement.disabled = busy || !state.active;
            if (state.next_role && part) {
                els.cameraTitle.textContent = `Готова камера ${roleTitle(state.next_role)}`;
            }
        }
        updatePaletteSelection();
    }

    function resetFrame() {
        currentFrame = null;
        annotations = [];
        draftPoints = [];
        draftClass = '';
        hoverPoint = null;
        noDefectSelected = false;
        els.wrap.classList.add('empty');
        els.wrap.style.aspectRatio = '16 / 9';
        els.image.removeAttribute('src');
        const ctx = els.canvas.getContext('2d');
        ctx.clearRect(0, 0, els.canvas.width, els.canvas.height);
        els.emptyState.classList.remove('hidden');
        els.frameId.textContent = 'FRAME —';
        els.frameRole.textContent = 'КАМЕРА —';
        els.frameSize.textContent = '— × —';
        els.cameraTitle.textContent = 'Ожидание корпуса';
        els.annotationHelp.textContent = 'Кликайте точки контура, затем нажмите «Завершить область»';
        els.classSelect.value = '';
        els.classSelect.disabled = true;
        els.finishPolygon.disabled = true;
        els.noDefect.disabled = true;
        els.clearBox.disabled = true;
        els.save.disabled = true;
        els.nextCamera.disabled = true;
        els.newElement.disabled = !(state && state.active);
        els.addElement.disabled = !(state && state.active);
        els.canvas.style.pointerEvents = 'none';
        updatePaletteSelection();
    }

    function showFrame(frame, annotated = false) {
        currentFrame = frame;
        annotations = [];
        draftPoints = [];
        draftClass = '';
        hoverPoint = null;
        noDefectSelected = false;
        els.wrap.classList.remove('empty');
        els.emptyState.classList.add('hidden');
        els.image.onload = () => {
            const width = els.image.naturalWidth || frame.width;
            const height = els.image.naturalHeight || frame.height;
            els.canvas.width = width;
            els.canvas.height = height;
            els.wrap.style.aspectRatio = `${width} / ${height}`;
            redrawAnnotations();
        };
        const url = (annotated && frame.annotated_url) ? frame.annotated_url : frame.original_url;
        els.image.src = `${url}${url.includes('?') ? '&' : '?'}v=${Date.now()}`;
        els.frameId.textContent = `FRAME #${frame.image_id}`;
        els.frameRole.textContent = roleTitle(frame.camera_role || frame.role || '—');
        els.frameSize.textContent = `${frame.width} × ${frame.height}`;
        const cell = frame.cell_id ? `ячейка ${frame.cell_id} · ` : '';
        els.cameraTitle.textContent = `${cell}${frame.camera_role || frame.role} · разметка`;
        els.annotationHelp.textContent = annotated
            ? 'Разметка сохранена. Можно переходить к следующей камере.'
            : 'Кликайте точки контура, затем нажмите «Завершить область»';
        els.canvas.style.pointerEvents = annotated ? 'none' : 'auto';
        els.classSelect.disabled = annotated;
        els.finishPolygon.disabled = annotated;
        els.noDefect.disabled = annotated;
        els.clearBox.disabled = annotated;
        els.save.disabled = annotated;
        els.nextCamera.disabled = !annotated;
        els.newElement.disabled = annotated || !(state && state.active);
        els.addElement.disabled = annotated || !(state && state.active);
        els.canvas.getContext('2d').clearRect(0, 0, els.canvas.width, els.canvas.height);
        updatePaletteSelection();
    }

    function canvasPoint(event) {
        const rect = els.canvas.getBoundingClientRect();
        return {
            x: Math.max(0, Math.min(els.canvas.width, (event.clientX - rect.left) * els.canvas.width / rect.width)),
            y: Math.max(0, Math.min(els.canvas.height, (event.clientY - rect.top) * els.canvas.height / rect.height)),
        };
    }

    function distance(left, right) {
        return Math.hypot(left.x - right.x, left.y - right.y);
    }

    function drawPolygon(ctx, points, className, index, draft = false) {
        if (!points.length) return;
        const hue = (index * 67) % 360;
        ctx.strokeStyle = `hsl(${hue}, 80%, 62%)`;
        ctx.fillStyle = `hsla(${hue}, 80%, 55%, ${draft ? '.08' : '.14'})`;
        ctx.lineWidth = Math.max(2, els.canvas.width / 600);
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
        if (!draft && points.length >= 3) {
            ctx.closePath();
            ctx.fill();
        }
        ctx.stroke();
        points.forEach((point) => {
            ctx.beginPath();
            ctx.fillStyle = `hsl(${hue}, 80%, 70%)`;
            ctx.arc(point.x, point.y, Math.max(4, els.canvas.width / 180), 0, Math.PI * 2);
            ctx.fill();
        });
        if (className) {
            ctx.fillStyle = `hsl(${hue}, 80%, 70%)`;
            ctx.font = `${Math.max(14, els.canvas.width / 75)}px Segoe UI, Arial`;
            ctx.fillText(className, points[0].x + 6, Math.max(18, points[0].y - 8));
        }
    }

    function redrawAnnotations() {
        const ctx = els.canvas.getContext('2d');
        ctx.clearRect(0, 0, els.canvas.width, els.canvas.height);
        annotations.forEach((annotation, index) => {
            drawPolygon(ctx, annotation.points, annotation.class_name, index);
        });
        if (draftPoints.length) {
            const preview = draftPoints.slice();
            if (hoverPoint) preview.push(hoverPoint);
            drawPolygon(ctx, preview, draftClass || els.classSelect.value, annotations.length, true);
        }
        els.finishPolygon.disabled = !annotationEditable() || draftPoints.length < 3;
    }

    function finishCurrentPolygon() {
        if (!draftPoints.length) {
            setMessage(els.annotationMessage, 'Сначала поставьте точки контура.', 'error');
            return false;
        }
        if (draftPoints.length < 3) {
            setMessage(els.annotationMessage, 'Для области нужно минимум три точки.', 'error');
            return false;
        }
        annotations.push({
            class_name: draftClass || els.classSelect.value,
            points: draftPoints.map((point) => ({x: point.x, y: point.y})),
        });
        draftPoints = [];
        draftClass = '';
        hoverPoint = null;
        redrawAnnotations();
        setMessage(els.annotationMessage, 'Область добавлена. Можно выбрать другой элемент.', 'ok');
        return true;
    }

    els.canvas.addEventListener('pointerdown', (event) => {
        if (!annotationEditable() || noDefectSelected) return;
        if (!els.classSelect.value) {
            setMessage(els.annotationMessage, 'Сначала выберите элемент в палитре.', 'error');
            return;
        }
        event.preventDefault();
        const point = canvasPoint(event);
        if (!draftPoints.length) draftClass = els.classSelect.value;
        const closeDistance = Math.max(8, els.canvas.width / 100);
        if (draftPoints.length >= 3 && distance(point, draftPoints[0]) <= closeDistance) {
            finishCurrentPolygon();
            return;
        }
        draftPoints.push(point);
        hoverPoint = null;
        redrawAnnotations();
    });

    els.canvas.addEventListener('pointermove', (event) => {
        if (!draftPoints.length || !annotationEditable()) return;
        hoverPoint = canvasPoint(event);
        redrawAnnotations();
    });

    els.canvas.addEventListener('pointerleave', () => {
        if (!hoverPoint) return;
        hoverPoint = null;
        redrawAnnotations();
    });

    els.canvas.addEventListener('dblclick', (event) => {
        event.preventDefault();
        finishCurrentPolygon();
    });

    els.finishPolygon.addEventListener('click', finishCurrentPolygon);

    els.classSelect.addEventListener('change', () => {
        if (draftPoints.length && els.classSelect.value !== draftClass) {
            els.classSelect.value = draftClass;
            setMessage(els.annotationMessage, 'Сначала завершите текущую область.', 'error');
            return;
        }
        noDefectSelected = false;
        els.noDefect.classList.remove('selected');
        updatePaletteSelection();
        redrawAnnotations();
    });

    els.noDefect.addEventListener('click', () => {
        draftPoints = [];
        draftClass = '';
        hoverPoint = null;
        annotations = [];
        noDefectSelected = true;
        els.classSelect.value = '';
        els.noDefect.classList.add('selected');
        updatePaletteSelection();
        redrawAnnotations();
    });

    els.clearBox.addEventListener('click', () => {
        annotations = [];
        draftPoints = [];
        draftClass = '';
        hoverPoint = null;
        noDefectSelected = false;
        els.classSelect.value = '';
        els.noDefect.classList.remove('selected');
        updatePaletteSelection();
        redrawAnnotations();
    });

    els.addElement.addEventListener('click', async () => {
        const name = els.newElement.value.trim();
        if (!name) {
            setMessage(els.annotationMessage, 'Введите название элемента палитры.', 'error');
            return;
        }
        els.addElement.disabled = true;
        try {
            const result = await api('/api/training/classes', {
                method: 'POST', body: JSON.stringify({class_name: name}),
            });
            fillClasses(result.defect_classes || []);
            selectElement(name);
            els.newElement.value = '';
            setMessage(els.annotationMessage, `Элемент «${name}» добавлен в палитру.`, 'ok');
        } catch (error) {
            setMessage(els.annotationMessage, error.message, 'error');
        } finally {
            els.addElement.disabled = !(state && state.active);
        }
    });

    els.newElement.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') els.addElement.click();
    });

    els.startCell.addEventListener('input', () => { els.startCell.dataset.touched = '1'; });

    async function loadCapture() {
        clearMessages();
        setBusy(true, 'Снимаем кадр…');
        try {
            const result = await api('/api/training/capture', {method: 'POST', body: '{}'});
            renderState(result.state);
            showFrame(result.frame, false);
            setMessage(els.annotationMessage,
                `Кадр #${result.frame.image_id} сохранён. Выберите элемент и поставьте точки контура.`, 'ok');
        } catch (error) {
            setMessage(els.annotationMessage, error.message, 'error');
            renderState(state);
        } finally {
            setBusy(false);
        }
    }

    function setBusy(value, message = '') {
        busy = Boolean(value);
        if (message) setMessage(els.workflowMessage, message);
        document.body.classList.toggle('busy', busy);
        renderState(state);
    }

    els.create.addEventListener('click', async () => {
        const roles = selectedValues(els.roles);
        const classes = els.classes.value.split(',').map((item) => item.trim()).filter(Boolean);
        const startCell = Number(els.startCell.value || 1);
        if (!roles.length) { setMessage(els.setupMessage, 'Выберите хотя бы одну камеру.', 'error'); return; }
        if (!classes.length) { setMessage(els.setupMessage, 'Укажите хотя бы один элемент палитры.', 'error'); return; }
        if (!Number.isInteger(startCell) || startCell < 1) {
            setMessage(els.setupMessage, 'Номер первого корпуса должен быть целым числом ≥ 1.', 'error');
            return;
        }
        els.create.disabled = true;
        try {
            const result = await api('/api/training/session', {
                method: 'POST',
                body: JSON.stringify({
                    dataset_name: els.datasetName.value.trim() || 'defects',
                    camera_roles: roles,
                    defect_classes: classes,
                    start_cell: startCell,
                }),
            });
            fillClasses(result.defect_classes || classes);
            renderState(result);
            els.setup.classList.add('hidden');
            els.work.classList.remove('hidden');
            setMessage(els.workflowMessage,
                'Набор создан. Нажмите «Снять следующий корпус» — станция встанет на его ячейку.', 'ok');
        } catch (error) {
            setMessage(els.setupMessage, error.message, 'error');
            els.create.disabled = false;
        }
    });

    els.newPart.addEventListener('click', async () => {
        setBusy(true, 'Станция едет на координаты ячейки…');
        try {
            const result = await api('/api/training/parts', {method: 'POST', body: '{}'});
            renderState(result);
            const part = result.part || {};
            const placement = part.cell_id
                ? `Ячейка ${part.cell_id} (ряд ${(part.row ?? 0) + 1}, колонка ${(part.column ?? 0) + 1}).`
                : 'Координаты не заданы.';
            setMessage(els.workflowMessage,
                `${placement} Корпус #${part.part_id} начат, снимаем ${roleTitle(result.next_role)}.`, 'ok');
            await loadCapture();
        } catch (error) {
            setMessage(els.workflowMessage, error.message, 'error');
            setBusy(false);
        }
    });

    els.stationHome.addEventListener('click', async () => {
        setBusy(true, 'Калибровка станции (G28)…');
        try {
            const result = await api('/api/training/home', {method: 'POST', body: '{}'});
            renderState(result);
            setMessage(els.workflowMessage, 'Станция откалибрована и припаркована.', 'ok');
        } catch (error) {
            setMessage(els.workflowMessage, error.message, 'error');
        } finally {
            setBusy(false);
        }
    });

    async function moveToCell(cellId) {
        if (busy) return;
        setBusy(true, `Станция едет в ячейку ${cellId}…`);
        try {
            const result = await api('/api/training/cells/move', {
                method: 'POST', body: JSON.stringify({cell_id: cellId}),
            });
            renderState(result);
            const movement = (result && result.movement) || {};
            const target = movement.target
                ? `X=${movement.target.x} Y=${movement.target.y} Z=${movement.target.z}`
                : '';
            setMessage(els.workflowMessage, movement.moved
                ? `Станция встала на ячейку ${cellId} (${target}). Можно начинать съёмку.`
                : `Станция отключена; ячейка ${cellId} выбрана для съёмки с текущей позиции.`,
                'ok');
        } catch (error) {
            setMessage(els.workflowMessage, error.message, 'error');
        } finally {
            setBusy(false);
        }
    }

    els.save.addEventListener('click', async () => {
        if (!currentFrame) return;
        if (draftPoints.length) {
            setMessage(els.annotationMessage, 'Сначала нажмите «Завершить область».', 'error');
            return;
        }
        if (!noDefectSelected && !annotations.length) {
            setMessage(els.annotationMessage,
                'Выберите элемент и обведите область. Если дефекта нет — нажмите «Дефекта нет».', 'error');
            return;
        }
        els.save.disabled = true;
        const wasNoDefect = noDefectSelected;
        try {
            const result = await api('/api/training/annotations', {
                method: 'POST',
                body: JSON.stringify({
                    image_id: currentFrame.image_id,
                    annotations: wasNoDefect ? [] : annotations,
                }),
            });
            renderState(result.state);
            showFrame(result.frame, true);
            setMessage(els.annotationMessage, wasNoDefect
                ? 'Кадр сохранён как отрицательный пример.'
                : 'Готово: оригинал и изображение с polygon-областями записаны.', 'ok');
            setMessage(els.workflowMessage, result.state.next_role
                ? `Готово. Следующая камера: ${roleTitle(result.state.next_role)}.`
                : 'Все три камеры корпуса сняты. Завершите корпус.', 'ok');
        } catch (error) {
            els.save.disabled = false;
            setMessage(els.annotationMessage, error.message, 'error');
        }
    });

    els.nextCamera.addEventListener('click', async () => {
        resetFrame();
        if (state && state.next_role) await loadCapture();
        else renderState(state);
    });

    els.finishPart.addEventListener('click', async () => {
        setBusy(true, 'Сохраняем корпус…');
        try {
            const result = await api('/api/training/parts/finish', {method: 'POST', body: '{}'});
            resetFrame();
            renderState(result);
            const partId = result.finished_part ? result.finished_part.part_id : '—';
            const nextCell = result.next_cell
                ? ` Следующая ячейка — ${result.next_cell.cell_id}.`
                : ' Все ячейки паллеты сняты.';
            setMessage(els.workflowMessage,
                `Корпус #${partId} сохранён.${nextCell} Нажмите «Снять следующий корпус».`, 'ok');
        } catch (error) {
            setMessage(els.workflowMessage, error.message, 'error');
        } finally {
            setBusy(false);
        }
    });

    els.export.addEventListener('click', async () => {
        try {
            const result = await api('/api/training/export', {method: 'POST', body: '{}'});
            setMessage(els.workflowMessage,
                `YOLO-${result.yolo.task || 'segment'}-экспорт обновлён: train ${result.yolo.train_count}, ` +
                `val ${result.yolo.validation_count}.`, 'ok');
        } catch (error) { setMessage(els.workflowMessage, error.message, 'error'); }
    });

    els.finishSession.addEventListener('click', async () => {
        if (!confirm('Завершить набор и подготовить структуру YOLO?')) return;
        setBusy(true);
        try {
            const result = await api('/api/training/session/finish', {
                method: 'POST', body: JSON.stringify({go_home: true}),
            });
            els.work.classList.add('hidden');
            els.result.classList.remove('hidden');
            const yolo = result.yolo || {};
            els.resultText.textContent = `Полигоны экспортированы: train (${yolo.train_count || 0}), ` +
                `val (${yolo.validation_count || 0}). Пустые label-файлы сохранены для кадров без дефекта.`;
            els.resultYaml.textContent = yolo.yaml_path || 'dataset.yaml создан в папке партии';
        } catch (error) {
            setMessage(els.workflowMessage, error.message, 'error');
        } finally {
            setBusy(false);
        }
    });

    function clearMessages() {
        setMessage(els.annotationMessage, '');
    }

    async function init() {
        try {
            const data = await api('/api/training/config');
            fillSetup(data);
            const existing = await api('/api/training/state');
            els.connection.textContent = 'СЕРВЕР ГОТОВ';
            els.connection.classList.add('ok');
            resetFrame();
            if (existing && existing.active && existing.session) {
                fillClasses(existing.defect_classes || data.defect_classes);
                renderState(existing);
                els.setup.classList.add('hidden');
                els.work.classList.remove('hidden');
                if (existing.current_frame) {
                    showFrame(existing.current_frame, false);
                    setMessage(els.annotationMessage,
                        'Сессия восстановлена. Продолжите обводку точками.', 'ok');
                } else {
                    setMessage(els.workflowMessage,
                        'Сессия восстановлена. Можно продолжить текущий корпус или начать следующий.', 'ok');
                }
            }
            if (existing) {
                // server запущен, но сессия ещё не создана: показываем
                // маршрут по паллете прямо в форме настройки.
                fillClasses(data.defect_classes || []);
                renderState(existing);
            }
        } catch (error) {
            els.connection.textContent = 'ОШИБКА СОЕДИНЕНИЯ';
            els.connection.classList.add('error');
            lastError = error.message;
            setMessage(els.setupMessage, error.message, 'error');
        }
    }

    init();
})();
