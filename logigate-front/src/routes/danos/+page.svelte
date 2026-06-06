<script>
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';
    import {
        ScanLine, Upload, ImagePlus, RotateCcw, History,
        AlertTriangle, CheckCircle, ShieldAlert, Camera,
        Clock, Percent, Layers, TrendingUp
    } from 'lucide-svelte';
    import { addToast } from '$lib/toast.svelte.js';

    const API = '';

    let modo = $state('camara');
    let videoEl = $state();
    let canvasEl = $state();
    let fileInput = $state();
    let stream = $state(null);
    let capturedImage = $state(null);
    let isAnalyzing = $state(false);
    let resultado = $state(null);
    let errorMsg = $state(null);
    let placa = $state('');
    let historial = $state([]);
    let activeTab = $state('scan');

    $effect(() => {
        if (videoEl && stream) videoEl.srcObject = stream;
    });

    onMount(async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        } catch (_) {}
        await fetchHistorial();
        return () => { stream?.getTracks().forEach(t => t.stop()); };
    });

    async function fetchHistorial() {
        try {
            const r = await fetch(`${API}/api/v1/damage-history?limit=20`);
            if (r.ok) historial = await r.json();
        } catch (_) {}
    }

    function resetear() {
        resultado = null; capturedImage = null; errorMsg = null;
        isAnalyzing = false; placa = '';
        if (fileInput) fileInput.value = '';
    }

    const takeSnapshot = () => {
        const ctx = canvasEl.getContext('2d');
        canvasEl.width = videoEl.videoWidth;
        canvasEl.height = videoEl.videoHeight;
        ctx.drawImage(videoEl, 0, 0);
        capturedImage = canvasEl.toDataURL('image/jpeg');
        sendBase64();
    };

    const handleFile = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        capturedImage = URL.createObjectURL(file);
        sendFile(file);
    };

    async function sendBase64() {
        isAnalyzing = true; errorMsg = null; resultado = null;
        try {
            const res = await fetch(capturedImage);
            const blob = await res.blob();
            await postDamage(blob, 'captura.jpg');
        } catch (e) {
            errorMsg = e.message || 'Error al enviar imagen.';
        } finally {
            isAnalyzing = false;
        }
    }

    async function sendFile(file) {
        isAnalyzing = true; errorMsg = null; resultado = null;
        try {
            await postDamage(file, file.name);
        } catch (e) {
            errorMsg = e.message || 'Error al enviar imagen.';
        } finally {
            isAnalyzing = false;
        }
    }

    async function postDamage(blob, name) {
        const fd = new FormData();
        fd.append('image', blob, name);
        if (placa.trim()) fd.append('placa', placa.trim().toUpperCase());
        const r = await fetch(`${API}/api/v1/damage-scan`, { method: 'POST', body: fd });
        if (!r.ok) {
            const err = await r.json().catch(() => ({ detail: `Error ${r.status}` }));
            const msg = typeof err.detail === 'string' ? err.detail : `Error ${r.status}`;
            throw new Error(msg);
        }
        resultado = await r.json();
        addToast(
            resultado.severidad === 'sin_danos'
                ? 'Sin daños detectados'
                : `${SEVERIDAD[resultado.severidad]?.label} detectado`,
            resultado.severidad === 'sin_danos' ? 'success' : resultado.severidad === 'grave' ? 'error' : 'info'
        );
        await fetchHistorial();
    }

    const SEVERIDAD = {
        sin_danos: { label: 'Sin Daños',      text: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20',  dot: 'bg-green-400'  },
        leve:      { label: 'Daño Leve',      text: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', dot: 'bg-yellow-400' },
        moderado:  { label: 'Daño Moderado',  text: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20', dot: 'bg-orange-400' },
        grave:     { label: 'Daño Grave',     text: 'text-red-400',    bg: 'bg-red-500/10',    border: 'border-red-500/20',    dot: 'bg-red-400'    },
    };

    const sev = $derived(resultado ? (SEVERIDAD[resultado.severidad] ?? SEVERIDAD.leve) : null);

    const fmtRelativo = (iso) => {
        if (!iso) return '';
        const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
        if (diff < 60) return 'Hace un momento';
        if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
        return `Hace ${Math.floor(diff / 3600)} h`;
    };
</script>

<div class="h-full bg-[#080A0E] text-white flex flex-col overflow-hidden">

    <!-- Tabs -->
    <div class="flex border-b border-slate-800/60 bg-[#0E1015] px-4 pt-4 gap-1 shrink-0">
        {#each [['scan','Inspeccionar'], ['historial','Historial']] as [tab, label]}
            <button
                onclick={() => activeTab = tab}
                class="px-4 py-2.5 text-xs font-black uppercase tracking-widest rounded-t-lg border-b-2 transition-all
                    {activeTab === tab
                        ? 'border-orange-500 text-orange-400 bg-orange-500/5'
                        : 'border-transparent text-slate-600 hover:text-slate-300'}"
            >
                {label}
            </button>
        {/each}
    </div>

    <div class="flex-grow overflow-y-auto custom-scrollbar">

        <!-- ── TAB: SCAN ── -->
        {#if activeTab === 'scan'}
            <div class="p-4 md:p-6 flex flex-col items-center gap-4" in:fade={{ duration: 100 }}>

                <!-- Placa opcional -->
                <div class="w-full max-w-md">
                    <label class="text-[9px] font-black uppercase tracking-widest text-slate-600 mb-1.5 block">
                        Placa del vehículo (opcional)
                    </label>
                    <input
                        bind:value={placa}
                        placeholder="Ej. ABC-123"
                        maxlength="10"
                        class="w-full bg-[#0E1015] border border-slate-800 rounded-xl px-4 py-2.5 text-sm font-bold text-white placeholder-slate-700 focus:outline-none focus:border-orange-500/50 uppercase tracking-widest"
                    />
                </div>

                <!-- Selector modo -->
                {#if !resultado && !isAnalyzing}
                    <div class="w-full max-w-md flex bg-[#0E1015] border border-slate-800/60 rounded-xl p-1">
                        <button
                            onclick={() => { modo = 'camara'; resetear(); }}
                            class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all
                                {modo === 'camara' ? 'bg-orange-500 text-black shadow-lg shadow-orange-500/20' : 'text-slate-500 hover:text-white'}"
                        >
                            <Camera size={14} /> Cámara
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

                <!-- Cámara -->
                {#if modo === 'camara' && !resultado && !isAnalyzing}
                    <div class="relative w-full max-w-md aspect-[4/3] bg-slate-900 rounded-2xl overflow-hidden border border-slate-800/60 shadow-2xl">
                        <video bind:this={videoEl} autoplay playsinline class="w-full h-full object-cover"></video>
                        <div class="absolute inset-0 pointer-events-none">
                            <div class="absolute inset-8 border border-orange-500/30 rounded-lg">
                                <div class="absolute top-0 left-0 w-5 h-5 border-t-2 border-l-2 border-orange-500 rounded-tl-sm"></div>
                                <div class="absolute top-0 right-0 w-5 h-5 border-t-2 border-r-2 border-orange-500 rounded-tr-sm"></div>
                                <div class="absolute bottom-0 left-0 w-5 h-5 border-b-2 border-l-2 border-orange-500 rounded-bl-sm"></div>
                                <div class="absolute bottom-0 right-0 w-5 h-5 border-b-2 border-r-2 border-orange-500 rounded-br-sm"></div>
                            </div>
                            <div class="absolute top-3 left-3 flex items-center gap-1.5 bg-black/50 px-2.5 py-1 rounded-full border border-orange-500/30">
                                <div class="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></div>
                                <span class="text-[10px] font-bold text-orange-400 tracking-wider">EN VIVO</span>
                            </div>
                        </div>
                    </div>
                {/if}

                <!-- Upload -->
                {#if modo === 'archivo' && !resultado && !isAnalyzing}
                    <div
                        class="w-full max-w-md bg-[#0E1015] rounded-2xl border-2 border-dashed border-slate-700 hover:border-orange-500/50 transition-all cursor-pointer overflow-hidden"
                        onclick={() => fileInput.click()}
                        onkeydown={(e) => e.key === 'Enter' && fileInput.click()}
                        role="button" tabindex="0"
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

                <!-- Procesando -->
                {#if isAnalyzing}
                    <div class="w-full max-w-md rounded-2xl overflow-hidden border border-orange-500/30 relative min-h-48">
                        {#if capturedImage}
                            <img src={capturedImage} alt="Analizando" class="w-full object-contain max-h-64 opacity-30" />
                        {/if}
                        <div class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/70">
                            <div class="w-12 h-12 border-2 border-slate-700 border-t-orange-500 rounded-full animate-spin"></div>
                            <p class="text-sm font-black text-white tracking-widest">ANALIZANDO DAÑOS</p>
                            <p class="text-[10px] text-orange-400">Motor IA · YOLO</p>
                        </div>
                    </div>
                {/if}

                <canvas bind:this={canvasEl} class="hidden"></canvas>
                <input bind:this={fileInput} type="file" accept="image/*" class="hidden" onchange={handleFile} />

                <!-- Botones de acción -->
                <div class="w-full max-w-md space-y-2">
                    {#if modo === 'camara' && !isAnalyzing && !resultado}
                        <button
                            onclick={takeSnapshot}
                            class="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] transition-all text-black font-black py-4 rounded-xl flex justify-center items-center gap-2.5 uppercase tracking-[0.1em] shadow-xl shadow-orange-500/25"
                        >
                            <ScanLine size={20} /> Capturar y Analizar Daños
                        </button>
                    {/if}

                    {#if modo === 'archivo' && !isAnalyzing && !resultado && capturedImage}
                        <button
                            onclick={() => sendFile(fileInput.files[0])}
                            class="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] transition-all text-black font-black py-4 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest shadow-xl shadow-orange-500/25"
                        >
                            <ScanLine size={20} /> Analizar Daños
                        </button>
                        <button
                            onclick={() => fileInput.click()}
                            class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-bold py-3 rounded-xl flex justify-center items-center gap-2 text-sm"
                        >
                            <ImagePlus size={16} /> Cambiar imagen
                        </button>
                    {/if}

                    <!-- Resultado -->
                    {#if resultado && sev}
                        <div class="bg-[#0E1015] rounded-2xl border {sev.border} overflow-hidden shadow-2xl" in:fade={{ duration: 150 }}>
                            <!-- Imagen anotada -->
                            {#if resultado.image_url}
                                <div class="relative">
                                    <img src="{API}{resultado.image_url}" alt="Resultado" class="w-full object-cover" />
                                    <div class="absolute inset-0 bg-gradient-to-t from-[#0E1015]/80 to-transparent pointer-events-none"></div>
                                </div>
                            {/if}

                            <div class="p-5 space-y-4">
                                <!-- Severidad -->
                                <div class="flex items-center gap-3">
                                    <div class="p-2.5 {sev.bg} border {sev.border} rounded-xl shrink-0">
                                        {#if resultado.severidad === 'sin_danos'}
                                            <CheckCircle size={22} class={sev.text} />
                                        {:else}
                                            <AlertTriangle size={22} class={sev.text} />
                                        {/if}
                                    </div>
                                    <div class="flex-grow">
                                        <p class="text-[10px] uppercase tracking-widest text-slate-500 font-black">Resultado de Inspección</p>
                                        <p class="text-xl font-black {sev.text}">{sev.label}</p>
                                        {#if resultado.placa}
                                            <p class="text-xs text-slate-600 mt-0.5">Placa: <span class="font-bold text-slate-400 tracking-wider">{resultado.placa}</span></p>
                                        {/if}
                                    </div>
                                    <span class="text-[10px] font-black px-2.5 py-1 rounded-full border {sev.bg} {sev.text} {sev.border} shrink-0">
                                        {sev.label.toUpperCase()}
                                    </span>
                                </div>

                                <!-- Stats -->
                                <div class="grid grid-cols-3 gap-2">
                                    <div class="bg-slate-800/30 rounded-xl p-3 border border-slate-800/60">
                                        <div class="flex items-center gap-1 mb-2">
                                            <Layers size={11} class="text-slate-600" />
                                            <p class="text-[8px] uppercase tracking-widest text-slate-600 font-black">Daños</p>
                                        </div>
                                        <p class="text-xl font-black {sev.text}">{resultado.danos_detectados}</p>
                                    </div>
                                    <div class="bg-slate-800/30 rounded-xl p-3 border border-slate-800/60">
                                        <div class="flex items-center gap-1 mb-2">
                                            <Percent size={11} class="text-slate-600" />
                                            <p class="text-[8px] uppercase tracking-widest text-slate-600 font-black">Área</p>
                                        </div>
                                        <p class="text-xl font-black {sev.text}">{resultado.damage_ratio}%</p>
                                    </div>
                                    <div class="bg-slate-800/30 rounded-xl p-3 border border-slate-800/60">
                                        <div class="flex items-center gap-1 mb-2">
                                            <TrendingUp size={11} class="text-slate-600" />
                                            <p class="text-[8px] uppercase tracking-widest text-slate-600 font-black">Confianza</p>
                                        </div>
                                        <p class="text-xl font-black {sev.text}">{resultado.confianza_promedio ?? 0}%</p>
                                    </div>
                                </div>

                                <!-- Detecciones individuales -->
                                {#if resultado.detecciones?.length > 0}
                                    <div>
                                        <p class="text-[9px] font-black uppercase tracking-widest text-slate-600 mb-2">Detecciones</p>
                                        <div class="space-y-1.5">
                                            {#each resultado.detecciones as det}
                                                <div class="flex items-center gap-3 bg-slate-800/30 rounded-lg px-3 py-2 border border-slate-800/50">
                                                    <div class="w-1.5 h-1.5 rounded-full {sev.dot} shrink-0"></div>
                                                    <span class="text-xs font-bold text-slate-300 capitalize flex-grow">{det.tipo}</span>
                                                    <div class="flex items-center gap-2">
                                                        <div class="w-16 bg-slate-700/50 h-1 rounded-full overflow-hidden">
                                                            <div class="h-full {sev.dot} rounded-full" style="width:{Math.round(det.confianza*100)}%"></div>
                                                        </div>
                                                        <span class="text-[10px] text-slate-500 font-bold w-8 text-right">{Math.round(det.confianza*100)}%</span>
                                                    </div>
                                                </div>
                                            {/each}
                                        </div>
                                    </div>
                                {/if}

                                <button
                                    onclick={resetear}
                                    class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
                                >
                                    <RotateCcw size={15} /> Nueva Inspección
                                </button>
                            </div>
                        </div>
                    {/if}

                    <!-- Error -->
                    {#if errorMsg && !isAnalyzing}
                        <div class="bg-red-500/5 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
                            <ShieldAlert size={18} class="text-red-400 shrink-0 mt-0.5" />
                            <div>
                                <p class="text-sm font-bold text-red-300">Error</p>
                                <p class="text-xs text-red-400/70 mt-0.5">{errorMsg}</p>
                            </div>
                        </div>
                        <button onclick={resetear} class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold py-3 rounded-xl flex justify-center items-center gap-2 text-sm">
                            <RotateCcw size={15} /> Intentar de nuevo
                        </button>
                    {/if}
                </div>
            </div>

        <!-- ── TAB: HISTORIAL ── -->
        {:else}
            <div class="p-4 md:p-6" in:fade={{ duration: 100 }}>
                <div class="flex items-center gap-2 mb-4">
                    <History size={14} class="text-slate-600" />
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-600">Inspecciones recientes</p>
                </div>

                {#if historial.length === 0}
                    <div class="flex flex-col items-center justify-center gap-3 py-20 text-slate-700">
                        <AlertTriangle size={32} />
                        <p class="text-sm">Sin inspecciones registradas</p>
                    </div>
                {:else}
                    <div class="space-y-3">
                        {#each historial as h}
                            {@const s = SEVERIDAD[h.severidad] ?? SEVERIDAD.leve}
                            <div class="bg-[#0E1015] border border-slate-800/60 rounded-2xl overflow-hidden hover:border-slate-700/60 transition-colors">
                                <div class="flex gap-3 p-3">
                                    {#if h.imagen_url}
                                        <img src="{API}{h.imagen_url}" alt="scan" class="w-20 h-16 object-cover rounded-xl shrink-0" />
                                    {:else}
                                        <div class="w-20 h-16 bg-slate-800 rounded-xl shrink-0 flex items-center justify-center">
                                            <AlertTriangle size={18} class="text-slate-600" />
                                        </div>
                                    {/if}
                                    <div class="flex-grow min-w-0">
                                        <div class="flex items-center gap-2 mb-1">
                                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full border {s.bg} {s.text} {s.border}">
                                                {s.label.toUpperCase()}
                                            </span>
                                            {#if h.placa}
                                                <span class="text-[10px] font-bold text-slate-400 tracking-wider bg-slate-800 px-2 py-0.5 rounded">{h.placa}</span>
                                            {/if}
                                        </div>
                                        <div class="flex items-center gap-3 text-[10px] text-slate-600">
                                            <span><span class="font-black {s.text}">{h.danos_detectados}</span> daños</span>
                                            <span><span class="font-black {s.text}">{h.damage_ratio}%</span> afectado</span>
                                        </div>
                                        <div class="flex items-center gap-1.5 mt-1.5">
                                            <Clock size={10} class="text-slate-700" />
                                            <span class="text-[10px] text-slate-700">{fmtRelativo(h.created_at)}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        {/if}
    </div>
</div>

<style>
    :global(.custom-scrollbar::-webkit-scrollbar) { width: 5px; }
    :global(.custom-scrollbar::-webkit-scrollbar-track) { background: #080A0E; }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: #1e2530; border-radius: 10px; }
</style>
