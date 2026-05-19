<script>
    import { onMount } from 'svelte';
    import { Scan, CheckCircle, XCircle, RotateCcw, Upload, ImagePlus, Shield, ShieldOff, History, Edit2, Check, Ban } from 'lucide-svelte';
    import { addToast } from '$lib/toast.svelte.js';
    import { settings } from '$lib/settings.svelte.js';

    const API = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000';
    const HIST_KEY = 'lg_scan_history';

    let videoSource = $state();
    let canvasElement = $state();
    let fileInput = $state();
    let isScanning = $state(false);
    let capturedImage = $state(null);
    let resultado = $state(null);
    let error = $state(null);
    let modo = $state('camara');
    let scanLinePos = $state(0);
    let scanInterval = null;
    let historial = $state([]);
    let overrideEstado = $state(null); // null | 'entrada' | 'denegado'
    let editandoPlaca  = $state(false);
    let placaEditada   = $state('');
    let stream         = $state(null);

    $effect(() => {
        if (videoSource && stream) videoSource.srcObject = stream;
    });

    function playBeep(authorized) {
        if (!settings.beep) return;
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime;
            if (authorized) {
                [[880, now, 0.25], [1100, now + 0.18, 0.25]].forEach(([freq, start, dur]) => {
                    const o = ctx.createOscillator();
                    const g = ctx.createGain();
                    o.connect(g); g.connect(ctx.destination);
                    o.frequency.value = freq; o.type = 'sine';
                    g.gain.setValueAtTime(0.15, start);
                    g.gain.exponentialRampToValueAtTime(0.001, start + dur);
                    o.start(start); o.stop(start + dur);
                });
            } else {
                const o = ctx.createOscillator();
                const g = ctx.createGain();
                o.connect(g); g.connect(ctx.destination);
                o.frequency.value = 280; o.type = 'square';
                g.gain.setValueAtTime(0.1, now);
                g.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
                o.start(now); o.stop(now + 0.5);
            }
        } catch (_) {}
    }

    function saveToHistory(r) {
        const entry = {
            plate: r.plate,
            status: r.status,
            esAutorizado: !r.status?.toLowerCase().includes('denegad') && !r.status?.toLowerCase().includes('error'),
            confPct: Math.round(r.confidence * 100),
            hora: new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' }),
        };
        historial = [entry, ...historial].slice(0, 5);
        if (typeof localStorage !== 'undefined')
            localStorage.setItem(HIST_KEY, JSON.stringify(historial));
    }

    onMount(async () => {
        if (typeof localStorage !== 'undefined') {
            try { historial = JSON.parse(localStorage.getItem(HIST_KEY) || '[]'); } catch (_) {}
        }
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        } catch (_) {
            error = 'No se pudo acceder a la cámara.';
        }
        return () => {};
    });

    function startScanLine() {
        let dir = 1;
        scanInterval = setInterval(() => {
            scanLinePos += dir * 2;
            if (scanLinePos >= 100) dir = -1;
            if (scanLinePos <= 0) dir = 1;
        }, 16);
    }

    function stopScanLine() {
        if (scanInterval) clearInterval(scanInterval);
        scanLinePos = 0;
    }

    const takeSnapshot = () => {
        const ctx = canvasElement.getContext('2d');
        canvasElement.width = videoSource.videoWidth;
        canvasElement.height = videoSource.videoHeight;
        ctx.drawImage(videoSource, 0, 0, canvasElement.width, canvasElement.height);
        capturedImage = canvasElement.toDataURL('image/jpeg');
        isScanning = true; resultado = null; error = null;
        startScanLine();
        sendToBackend(capturedImage);
    };

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        capturedImage = URL.createObjectURL(file);
        isScanning = true; resultado = null; error = null;
        startScanLine();
        sendFileToBackend(file);
    };

    async function postScan(fd) {
        const r = await fetch(`${API}/api/v1/scan`, { method: 'POST', body: fd });
        if (!r.ok) throw new Error(`Error ${r.status}`);
        return r.json();
    }

    const sendToBackend = async (base64) => {
        try {
            const res = await fetch(base64);
            const blob = await res.blob();
            const fd = new FormData();
            fd.append('image', blob, 'captura.jpg');
            resultado = await postScan(fd);
            const auth = !resultado.status?.toLowerCase().includes('denegad') && !resultado.status?.toLowerCase().includes('error');
            playBeep(auth);
            addToast(auth ? `Acceso concedido: ${resultado.plate}` : `Acceso denegado: ${resultado.plate}`, auth ? 'success' : 'error');
            saveToHistory(resultado);
        } catch (_) {
            error = 'No se pudo conectar con el servidor de IA.';
            addToast('Error al conectar con el servidor', 'error');
        } finally {
            isScanning = false; stopScanLine();
        }
    };

    const sendFileToBackend = async (file) => {
        try {
            const fd = new FormData();
            fd.append('image', file, file.name);
            resultado = await postScan(fd);
            const auth = !resultado.status?.toLowerCase().includes('denegad') && !resultado.status?.toLowerCase().includes('error');
            playBeep(auth);
            addToast(auth ? `Acceso concedido: ${resultado.plate}` : `Acceso denegado: ${resultado.plate}`, auth ? 'success' : 'error');
            saveToHistory(resultado);
        } catch (_) {
            error = 'No se pudo conectar con el servidor de IA.';
            addToast('Error al conectar con el servidor', 'error');
        } finally {
            isScanning = false; stopScanLine();
        }
    };

    const resetear = () => {
        resultado = null; capturedImage = null; error = null;
        isScanning = false; stopScanLine();
        overrideEstado = null; editandoPlaca = false; placaEditada = '';
        if (fileInput) fileInput.value = '';
    };

    const esAutorizado = $derived(
        overrideEstado != null
            ? overrideEstado === 'entrada'
            : resultado && !resultado.status?.toLowerCase().includes('denegad') && !resultado.status?.toLowerCase().includes('error')
    );
    const placaMostrada = $derived(editandoPlaca ? placaEditada : resultado?.plate ?? '');
    const confPct = $derived(resultado ? Math.round(resultado.confidence * 100) : 0);

    function aceptar() {
        overrideEstado = 'entrada';
        editandoPlaca  = false;
        playBeep(true);
        addToast(`Acceso concedido manualmente: ${placaMostrada}`, 'success');
    }

    function denegar() {
        overrideEstado = 'denegado';
        editandoPlaca  = false;
        playBeep(false);
        addToast(`Acceso denegado manualmente: ${placaMostrada}`, 'error');
    }

    function iniciarEdicion() {
        placaEditada  = resultado?.plate ?? '';
        editandoPlaca = true;
    }

    function confirmarEdicion() {
        if (!placaEditada.trim()) return;
        resultado = { ...resultado, plate: placaEditada.trim().toUpperCase() };
        editandoPlaca = false;
        addToast(`Placa corregida: ${resultado.plate}`, 'info');
    }
</script>

<div class="h-full bg-[#080A0E] text-white p-4 md:p-6 flex flex-col items-center overflow-y-auto custom-scrollbar">

    <!-- Selector de modo -->
    {#if !resultado && !isScanning}
        <div class="w-full max-w-md flex bg-[#0E1015] border border-slate-800/60 rounded-xl p-1 mb-5 mt-1">
            <button
                onclick={() => { modo = 'camara'; resetear(); }}
                class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all
                    {modo === 'camara' ? 'bg-orange-500 text-black shadow-lg shadow-orange-500/20' : 'text-slate-500 hover:text-white'}"
            >
                <Scan size={14} /> Cámara
            </button>
            <button
                onclick={() => { modo = 'archivo'; resetear(); }}
                class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all
                    {modo === 'archivo' ? 'bg-orange-500 text-black shadow-lg shadow-orange-500/20' : 'text-slate-500 hover:text-white'}"
            >
                <ImagePlus size={14} /> Subir Foto
            </button>
        </div>
    {/if}

    <!-- Vista cámara -->
    {#if modo === 'camara' && !resultado}
        <div class="relative w-full max-w-md aspect-[4/3] bg-slate-900 rounded-2xl overflow-hidden border border-slate-800/60 shadow-2xl">
            <video bind:this={videoSource} autoplay playsinline class="w-full h-full object-cover"></video>
            <div class="absolute inset-0 pointer-events-none">
                <div class="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/30"></div>
                <div class="absolute inset-8 border border-orange-500/30 rounded-lg">
                    <div class="absolute top-0 left-0 w-5 h-5 border-t-2 border-l-2 border-orange-500 rounded-tl-sm"></div>
                    <div class="absolute top-0 right-0 w-5 h-5 border-t-2 border-r-2 border-orange-500 rounded-tr-sm"></div>
                    <div class="absolute bottom-0 left-0 w-5 h-5 border-b-2 border-l-2 border-orange-500 rounded-bl-sm"></div>
                    <div class="absolute bottom-0 right-0 w-5 h-5 border-b-2 border-r-2 border-orange-500 rounded-br-sm"></div>
                </div>
                {#if isScanning}
                    <div
                        class="absolute left-8 right-8 h-px bg-gradient-to-r from-transparent via-orange-500 to-transparent shadow-[0_0_8px_2px_rgba(249,115,22,0.6)] transition-none"
                        style="top: calc(2rem + {scanLinePos}%)"
                    ></div>
                {/if}
                <div class="absolute top-3 left-3 flex items-center gap-1.5 bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-full border border-orange-500/30">
                    <div class="w-1.5 h-1.5 rounded-full bg-orange-500 {isScanning ? 'animate-pulse' : ''}"></div>
                    <span class="text-[10px] font-bold text-orange-400 tracking-wider">{isScanning ? 'PROCESANDO' : 'EN VIVO'}</span>
                </div>
            </div>
        </div>
    {/if}

    <!-- Vista subir archivo -->
    {#if modo === 'archivo' && !resultado && !isScanning}
        <div
            class="w-full max-w-md bg-[#0E1015] rounded-2xl border-2 border-dashed border-slate-700 hover:border-orange-500/50 transition-all cursor-pointer overflow-hidden"
            onclick={() => fileInput.click()}
            onkeydown={(e) => e.key === 'Enter' && fileInput.click()}
            role="button"
            tabindex="0"
        >
            {#if capturedImage}
                <img src={capturedImage} alt="Vista previa" class="w-full object-contain max-h-64" />
            {:else}
                <div class="flex flex-col items-center justify-center gap-3 p-12">
                    <div class="p-4 bg-slate-800/50 rounded-2xl">
                        <Upload size={28} class="text-slate-500" />
                    </div>
                    <div class="text-center">
                        <p class="text-slate-400 text-sm font-bold">Toca para seleccionar</p>
                        <p class="text-slate-600 text-xs mt-1">JPG, PNG, WEBP · máx. 10 MB</p>
                    </div>
                </div>
            {/if}
        </div>
    {/if}

    <!-- Procesando overlay -->
    {#if isScanning && capturedImage}
        <div class="w-full max-w-md rounded-2xl overflow-hidden border border-orange-500/30 relative">
            <img src={capturedImage} alt="Procesando" class="w-full object-contain max-h-64 opacity-50" />
            <div class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/60 backdrop-blur-sm">
                <div class="w-12 h-12 border-2 border-slate-700 border-t-orange-500 rounded-full animate-spin"></div>
                <div class="text-center">
                    <p class="text-sm font-black text-white tracking-widest">ANALIZANDO</p>
                    <p class="text-[10px] text-orange-400 mt-1">Motor IA · YOLOv11 + EasyOCR</p>
                </div>
                <div class="w-48 bg-slate-800 h-1 rounded-full overflow-hidden mt-2">
                    <div class="h-full bg-orange-500 rounded-full animate-[scan_1.5s_ease-in-out_infinite]"></div>
                </div>
            </div>
        </div>
    {/if}

    <canvas bind:this={canvasElement} class="hidden"></canvas>
    <input bind:this={fileInput} type="file" accept="image/*" class="hidden" onchange={handleFileUpload} />

    <!-- Acciones -->
    <div class="mt-5 w-full max-w-md space-y-3">

        {#if modo === 'camara' && !isScanning && !resultado}
            <button
                onclick={takeSnapshot}
                class="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] transition-all text-black font-black py-4 rounded-xl flex justify-center items-center gap-2.5 uppercase tracking-[0.1em] shadow-xl shadow-orange-500/25"
            >
                <Scan size={22} /> Capturar y Analizar
            </button>
        {/if}

        {#if modo === 'archivo' && !isScanning && !resultado && capturedImage}
            <button
                onclick={() => { sendFileToBackend(fileInput.files[0]); isScanning = true; startScanLine(); }}
                class="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] transition-all text-black font-black py-4 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest shadow-xl shadow-orange-500/25"
            >
                <Scan size={20} /> Analizar imagen
            </button>
            <button
                onclick={() => fileInput.click()}
                class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all text-slate-300 font-bold py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
            >
                <ImagePlus size={16} /> Cambiar imagen
            </button>
        {/if}

        <!-- Resultado -->
        {#if resultado}
            <div class="bg-[#0E1015] rounded-2xl border {esAutorizado ? 'border-green-500/30' : 'border-red-500/30'} overflow-hidden shadow-2xl">
                {#if resultado.image_url}
                    <div class="relative">
                        <img src="{API}{resultado.image_url}" alt="Placa capturada" class="w-full object-cover max-h-40" />
                        <div class="absolute inset-0 bg-gradient-to-t from-[#0E1015] to-transparent"></div>
                    </div>
                {/if}
                <div class="p-5 space-y-4">
                    <div class="flex items-center gap-3">
                        <div class="p-2.5 {esAutorizado ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'} rounded-xl border shrink-0">
                            {#if esAutorizado}
                                <Shield size={22} class="text-green-400" />
                            {:else}
                                <ShieldOff size={22} class="text-red-400" />
                            {/if}
                        </div>
                        <div class="flex-grow min-w-0">
                            <p class="text-[10px] uppercase tracking-widest text-slate-500 font-black">Placa Detectada</p>
                            {#if editandoPlaca}
                                <div class="flex items-center gap-2 mt-1">
                                    <input
                                        bind:value={placaEditada}
                                        onkeydown={(e) => e.key === 'Enter' && confirmarEdicion()}
                                        class="bg-slate-800 border border-orange-500/50 rounded-lg px-3 py-1.5 text-lg font-black text-white tracking-[0.15em] uppercase w-36 focus:outline-none focus:border-orange-500"
                                        maxlength="10"
                                        autofocus
                                    />
                                    <button onclick={confirmarEdicion} class="p-1.5 bg-green-500/15 border border-green-500/30 rounded-lg text-green-400 hover:bg-green-500/25 transition-colors">
                                        <Check size={16} />
                                    </button>
                                    <button onclick={() => editandoPlaca = false} class="p-1.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-500 hover:text-white transition-colors">
                                        <XCircle size={16} />
                                    </button>
                                </div>
                            {:else}
                                <p class="text-2xl font-black text-white tracking-[0.15em]">{placaMostrada}</p>
                                {#if overrideEstado}
                                    <p class="text-[9px] text-slate-600 mt-0.5">Override manual · IA original: {resultado.plate}</p>
                                {/if}
                            {/if}
                        </div>
                        <div class="ml-auto shrink-0">
                            <span class="text-[10px] font-black px-2.5 py-1 rounded-full border {esAutorizado ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}">
                                {esAutorizado ? 'AUTORIZADO' : 'DENEGADO'}
                            </span>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-slate-800/30 rounded-xl p-3.5 border border-slate-800/60">
                            <p class="text-[9px] uppercase tracking-widest text-slate-600 font-black mb-2">Confianza IA</p>
                            <p class="text-xl font-black text-orange-400 mb-2">{confPct}%</p>
                            <div class="w-full bg-slate-700/50 h-1 rounded-full overflow-hidden">
                                <div class="h-full bg-orange-500 rounded-full" style="width:{confPct}%"></div>
                            </div>
                        </div>
                        <div class="bg-slate-800/30 rounded-xl p-3.5 border border-slate-800/60">
                            <p class="text-[9px] uppercase tracking-widest text-slate-600 font-black mb-2">Estado</p>
                            <p class="text-xs font-bold {esAutorizado ? 'text-green-400' : 'text-red-400'} leading-snug">{resultado.status}</p>
                        </div>
                    </div>
                    <!-- Acciones de override -->
                    <div class="grid grid-cols-2 gap-2">
                        {#if !esAutorizado}
                            <button
                                onclick={aceptar}
                                class="flex items-center justify-center gap-2 bg-green-500/15 hover:bg-green-500/25 border border-green-500/30 text-green-400 font-black py-3 rounded-xl transition-all text-xs uppercase tracking-wider"
                            >
                                <Check size={15} /> Aceptar
                            </button>
                        {:else}
                            <button
                                onclick={denegar}
                                class="flex items-center justify-center gap-2 bg-red-500/15 hover:bg-red-500/25 border border-red-500/30 text-red-400 font-black py-3 rounded-xl transition-all text-xs uppercase tracking-wider"
                            >
                                <Ban size={15} /> Denegar
                            </button>
                        {/if}
                        <button
                            onclick={iniciarEdicion}
                            disabled={editandoPlaca}
                            class="flex items-center justify-center gap-2 bg-slate-800/60 hover:bg-slate-700 border border-slate-700 text-slate-300 font-bold py-3 rounded-xl transition-all text-xs uppercase tracking-wider disabled:opacity-40"
                        >
                            <Edit2 size={14} /> Corregir
                        </button>
                    </div>
                    <button
                        onclick={resetear}
                        class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all text-white font-bold py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
                    >
                        <RotateCcw size={15} /> Nueva Captura
                    </button>
                </div>
            </div>
        {/if}

        <!-- Error -->
        {#if error && !isScanning}
            <div class="bg-red-500/5 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
                <XCircle size={18} class="text-red-400 shrink-0 mt-0.5" />
                <div>
                    <p class="text-sm font-bold text-red-300">Error de conexión</p>
                    <p class="text-xs text-red-400/70 mt-0.5">{error}</p>
                </div>
            </div>
            <button
                onclick={resetear}
                class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all text-white font-bold py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
            >
                <RotateCcw size={15} /> Intentar de nuevo
            </button>
        {/if}

    </div>

    <!-- Historial últimas 5 -->
    {#if historial.length > 0}
        <div class="w-full max-w-md mt-6">
            <div class="flex items-center gap-2 mb-3">
                <History size={14} class="text-slate-600" />
                <p class="text-[10px] font-black uppercase tracking-widest text-slate-600">Últimos escaneos</p>
            </div>
            <div class="space-y-2">
                {#each historial as h}
                    <div class="flex items-center gap-3 bg-[#0E1015] border border-slate-800/50 rounded-xl px-3.5 py-2.5">
                        <span class="font-black text-white tracking-wider text-xs bg-slate-800 px-2 py-0.5 rounded">{h.plate}</span>
                        <span class="text-[10px] font-black px-2 py-0.5 rounded-full border
                            {h.esAutorizado ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}">
                            {h.esAutorizado ? 'OK' : 'DENY'}
                        </span>
                        <span class="text-[10px] text-slate-600 ml-auto">{h.hora} · {h.confPct}%</span>
                    </div>
                {/each}
            </div>
        </div>
    {/if}

</div>

<style>
    @keyframes scan {
        0%   { width: 0%; margin-left: 0; }
        50%  { width: 100%; margin-left: 0; }
        100% { width: 0%; margin-left: 100%; }
    }
</style>
