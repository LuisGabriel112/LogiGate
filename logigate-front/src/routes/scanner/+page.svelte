<script>
    import { onMount, onDestroy } from 'svelte';
    import {
        Camera, ShieldCheck, ShieldX, AlertTriangle,
        Edit3, Check, CheckSquare, Square, ChevronUp, ChevronDown, X
    } from 'lucide-svelte';

    const API = 'https://192.168.1.68:8000';

    // ── Cámara ────────────────────────────────────────────────
    let videoElMobile  = $state(null);
    let videoElDesktop = $state(null);
    let canvasEl = $state(null);
    let stream   = null;
    let camaraError = $state(false);

    // Asigna el stream a ambos elementos cuando estén disponibles
    $effect(() => {
        if (stream) {
            if (videoElMobile)  videoElMobile.srcObject  = stream;
            if (videoElDesktop) videoElDesktop.srcObject = stream;
        }
    });

    // ── Estado del escaneo ────────────────────────────────────
    let scanning    = $state(false);
    let scanResult  = $state(null);   // resultado del backend
    let captureUrl  = $state(null);   // preview de la captura
    let panelAbierto = $state(false); // bottom sheet visible

    // ── Campos editables ──────────────────────────────────────
    let placa        = $state('');
    let editingPlaca = $state(false);
    let empresa      = $state('');
    let tipoUnidad   = $state('');
    let conductor    = $state('');
    let danosVis     = $state(false);
    let sellosRot    = $state(false);
    let notas        = $state('');

    // ── Feedback ──────────────────────────────────────────────
    let actionMsg   = $state('');
    let actionType  = $state('');
    let saving      = $state(false);

    const token    = () => localStorage.getItem('token') || '';
    const userInfo = () => { try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; } };

    const confColor = (c) =>
        c >= 85 ? 'text-green-400' : c >= 60 ? 'text-yellow-400' : 'text-red-400';
    const confBg = (c) =>
        c >= 85 ? 'bg-green-500/15 border-green-500/30'
        : c >= 60 ? 'bg-yellow-500/15 border-yellow-500/30'
        : 'bg-red-500/15 border-red-500/30';
    const confLabel = (c) =>
        c >= 85 ? 'Alta' : c >= 60 ? 'Media' : 'Baja';

    // ── Iniciar cámara ────────────────────────────────────────
    onMount(async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: { ideal: 'environment' },
                    width:  { ideal: 1920, min: 1280 },
                    height: { ideal: 1080, min: 720  },
                }
            });
            if (videoElMobile)  videoElMobile.srcObject  = stream;
            if (videoElDesktop) videoElDesktop.srcObject = stream;
        } catch {
            camaraError = true;
        }
    });

    onDestroy(() => stream?.getTracks().forEach(t => t.stop()));

    // ── Captura y envío al backend ────────────────────────────
    async function capturar() {
        if (scanning) return;
        scanning     = true;
        scanResult   = null;
        panelAbierto = false;
        actionMsg    = '';

        // Capturar frame a resolución completa del video
        const activeVideo = videoElMobile ?? videoElDesktop;
        const ctx = canvasEl.getContext('2d');
        canvasEl.width  = activeVideo.videoWidth  || 1280;
        canvasEl.height = activeVideo.videoHeight || 720;
        ctx.drawImage(activeVideo, 0, 0, canvasEl.width, canvasEl.height);

        const blob = await new Promise(r => canvasEl.toBlob(r, 'image/jpeg', 0.95));
        captureUrl = URL.createObjectURL(blob);

        try {
            const fd = new FormData();
            fd.append('image', blob, 'placa.jpg');

            const res = await fetch(`${API}/api/v1/scan`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token()}` },
                body: fd,
            });
            if (!res.ok) throw new Error();

            const data = await res.json();
            scanResult   = data;
            placa        = data.placa;
            tipoUnidad   = data.tipo_unidad;
            empresa      = '';
            conductor    = '';
            danosVis     = false;
            sellosRot    = false;
            notas        = '';
            panelAbierto = true;   // abrir bottom sheet con resultados
        } catch {
            actionMsg    = 'Error al procesar la imagen. Intenta de nuevo.';
            actionType   = 'err';
            panelAbierto = true;
        } finally {
            scanning = false;
        }
    }

    // ── Persistir registro ────────────────────────────────────
    async function guardarRegistro(estado) {
        saving    = true;
        actionMsg = '';
        try {
            const res = await fetch(`${API}/api/v1/registros`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
                body: JSON.stringify({
                    placa, empresa, tipo_unidad: tipoUnidad, conductor, estado,
                    confianza: scanResult?.confianza ?? null,
                    danos_visibles: danosVis, sellos_rotos: sellosRot, notas,
                }),
            });
            if (!res.ok) throw new Error();

            const labels = { entrada: 'Acceso autorizado', denegado: 'Acceso denegado', salida: 'Salida registrada' };
            actionMsg  = `${labels[estado]} — ${placa}`;
            actionType = estado === 'denegado' ? 'err' : 'ok';

            setTimeout(() => {
                scanResult   = null;
                captureUrl   = null;
                actionMsg    = '';
                placa        = '';
                panelAbierto = false;
            }, 2500);
        } catch {
            actionMsg  = 'No se pudo guardar. Intenta de nuevo.';
            actionType = 'err';
        } finally {
            saving = false;
        }
    }

    function cerrarPanel() {
        panelAbierto = false;
        scanResult   = null;
        captureUrl   = null;
        placa        = '';
    }
</script>

<!-- ══════════════════════════════════════════════════════════
     LAYOUT MÓVIL: cámara pantalla completa + bottom sheet
     LAYOUT DESKTOP (md+): dos columnas
════════════════════════════════════════════════════════════ -->

<!-- ── VISTA MÓVIL ── -->
<div class="md:hidden relative flex flex-col h-full bg-black overflow-hidden">

    <!-- Cámara / feed -->
    <div class="relative flex-1 overflow-hidden">
        {#if camaraError}
            <div class="absolute inset-0 flex flex-col items-center justify-center gap-4 text-slate-500 p-8 text-center">
                <Camera size={48} class="opacity-30" />
                <p class="text-sm font-bold">No se pudo acceder a la cámara.</p>
                <p class="text-xs">Verifica los permisos del navegador.</p>
            </div>
        {:else}
            <video bind:this={videoElMobile} autoplay playsinline muted
                class="absolute inset-0 w-full h-full object-cover"></video>
        {/if}

        <!-- Visor con brackets -->
        <div class="absolute inset-0 pointer-events-none">
            <!-- Oscurecimiento lateral -->
            <div class="absolute inset-0 bg-black/25"></div>
            <!-- Zona de enfoque central -->
            <div class="absolute inset-x-8 top-[20%] bottom-[30%]">
                <div class="absolute top-0 left-0 w-8 h-8 border-t-[3px] border-l-[3px] border-orange-500"></div>
                <div class="absolute top-0 right-0 w-8 h-8 border-t-[3px] border-r-[3px] border-orange-500"></div>
                <div class="absolute bottom-0 left-0 w-8 h-8 border-b-[3px] border-l-[3px] border-orange-500"></div>
                <div class="absolute bottom-0 right-0 w-8 h-8 border-b-[3px] border-r-[3px] border-orange-500"></div>
                <!-- Línea de escaneo animada -->
                {#if !scanning && !scanResult}
                    <div class="scanline absolute inset-x-0 h-0.5 bg-gradient-to-r from-transparent via-orange-500 to-transparent opacity-70"></div>
                {/if}
            </div>
            <!-- Etiqueta guía -->
            <div class="absolute top-[18%] inset-x-0 flex justify-center">
                <span class="text-[11px] font-black uppercase tracking-widest text-orange-400/80">
                    {scanning ? 'Procesando...' : 'Apunta a la placa del vehículo'}
                </span>
            </div>
        </div>

        <!-- Badge cámara activa -->
        <div class="absolute top-3 right-3 flex items-center gap-1.5 bg-black/60 px-2.5 py-1 rounded-full">
            <div class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>
            <span class="text-[10px] font-bold text-white">LIVE</span>
        </div>

        <!-- Spinner de procesamiento -->
        {#if scanning}
            <div class="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/60">
                <div class="w-12 h-12 border-4 border-orange-500/30 border-t-orange-500 rounded-full animate-spin"></div>
                <p class="text-orange-400 font-black uppercase tracking-widest text-sm">Analizando placa...</p>
            </div>
        {/if}
    </div>

    <!-- Botón de captura flotante -->
    {#if !panelAbierto}
        <div class="absolute bottom-6 inset-x-0 flex flex-col items-center gap-3 px-6">
            {#if actionMsg && !panelAbierto}
                <div class="w-full px-4 py-2.5 rounded-xl text-center text-sm font-bold
                    {actionType === 'ok' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}">
                    {actionMsg}
                </div>
            {/if}
            <button
                onclick={capturar}
                disabled={scanning || camaraError}
                class="w-20 h-20 rounded-full bg-orange-500 hover:bg-orange-600 active:scale-95 disabled:opacity-50
                       flex items-center justify-center shadow-2xl shadow-orange-500/40 transition-all border-4 border-white/20"
            >
                <Camera size={32} class="text-black" />
            </button>
            <p class="text-[10px] text-white/40 font-bold uppercase tracking-widest">Capturar</p>
        </div>
    {/if}

    <!-- ── Bottom Sheet de resultados ── -->
    {#if panelAbierto}
        <div class="absolute bottom-0 inset-x-0 bg-[#1A1F26] rounded-t-3xl border-t border-slate-700 shadow-2xl z-20
                    flex flex-col max-h-[80vh]">

            <!-- Handle + header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-slate-800 shrink-0">
                <div class="flex items-center gap-3">
                    <h3 class="text-white font-black uppercase tracking-widest text-sm">Resultado</h3>
                    {#if scanResult}
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full border {confBg(scanResult.confianza)} {confColor(scanResult.confianza)}">
                            IA {confLabel(scanResult.confianza)} · {scanResult.confianza}%
                        </span>
                    {/if}
                </div>
                <button onclick={cerrarPanel} class="p-1.5 rounded-full bg-slate-800 text-slate-400">
                    <X size={18} />
                </button>
            </div>

            <!-- Contenido scrolleable -->
            <div class="overflow-y-auto flex-1 p-5 space-y-4">

                {#if actionMsg}
                    <div class="px-4 py-3 rounded-xl text-center text-sm font-bold border
                        {actionType === 'ok' ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}">
                        {actionMsg}
                    </div>
                {/if}

                <!-- Placa detectada -->
                <div class="bg-[#0D1117] rounded-2xl p-4 border border-slate-800">
                    <p class="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-2">Placa Detectada</p>
                    <div class="flex items-center gap-3">
                        {#if editingPlaca}
                            <input bind:value={placa} onblur={() => editingPlaca = false} autofocus
                                class="flex-1 bg-transparent text-3xl font-black text-white tracking-[0.2em] uppercase focus:outline-none border-b-2 border-orange-500 pb-1" />
                        {:else}
                            <span class="flex-1 text-3xl font-black text-white tracking-[0.2em]">
                                {placa || '— — —'}
                            </span>
                        {/if}
                        <button onclick={() => editingPlaca = !editingPlaca}
                            class="p-2 bg-slate-800 rounded-xl text-slate-400">
                            <Edit3 size={18} />
                        </button>
                    </div>
                    {#if tipoUnidad}
                        <p class="text-xs text-slate-500 mt-2 font-bold">{tipoUnidad}</p>
                    {/if}
                </div>

                <!-- Campos rápidos -->
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">Empresa</label>
                        <input bind:value={empresa} placeholder="Transportes..."
                            class="w-full bg-[#0D1117] border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-orange-500 transition-colors" />
                    </div>
                    <div>
                        <label class="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">Conductor</label>
                        <input bind:value={conductor} placeholder="Nombre..."
                            class="w-full bg-[#0D1117] border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-orange-500 transition-colors" />
                    </div>
                </div>

                <!-- Inspección -->
                <div class="grid grid-cols-2 gap-2">
                    <button onclick={() => danosVis = !danosVis}
                        class="flex items-center gap-2 p-3 rounded-xl border transition-all
                            {danosVis ? 'border-red-500/50 bg-red-500/10' : 'border-slate-800 bg-[#0D1117]'}">
                        {#if danosVis}<CheckSquare size={16} class="text-red-400 shrink-0" />
                        {:else}<Square size={16} class="text-slate-600 shrink-0" />{/if}
                        <span class="text-xs font-bold {danosVis ? 'text-red-400' : 'text-slate-500'}">Daños</span>
                    </button>
                    <button onclick={() => sellosRot = !sellosRot}
                        class="flex items-center gap-2 p-3 rounded-xl border transition-all
                            {sellosRot ? 'border-red-500/50 bg-red-500/10' : 'border-slate-800 bg-[#0D1117]'}">
                        {#if sellosRot}<CheckSquare size={16} class="text-red-400 shrink-0" />
                        {:else}<Square size={16} class="text-slate-600 shrink-0" />{/if}
                        <span class="text-xs font-bold {sellosRot ? 'text-red-400' : 'text-slate-500'}">Sellos Rotos</span>
                    </button>
                </div>
            </div>

            <!-- Botones de acción fijos en la parte baja -->
            <div class="p-4 pt-2 space-y-2 border-t border-slate-800 shrink-0 bg-[#1A1F26]">
                <button onclick={() => guardarRegistro('entrada')} disabled={!scanResult || saving}
                    class="w-full bg-orange-500 hover:bg-orange-600 active:scale-[0.98] disabled:opacity-40
                           text-black font-black py-4 rounded-2xl flex items-center justify-center gap-2 uppercase tracking-widest text-sm
                           shadow-lg shadow-orange-500/30 transition-all">
                    <ShieldCheck size={22} /> Autorizar Acceso
                </button>
                <div class="grid grid-cols-2 gap-2">
                    <button onclick={() => guardarRegistro('denegado')} disabled={!scanResult || saving}
                        class="bg-red-600/20 border border-red-600/40 text-red-400 font-black py-3.5 rounded-2xl
                               flex items-center justify-center gap-2 text-xs uppercase tracking-wide transition-all
                               disabled:opacity-40 active:scale-[0.98]">
                        <ShieldX size={16} /> Denegar
                    </button>
                    <button onclick={() => guardarRegistro('denegado')} disabled={!scanResult || saving}
                        class="bg-yellow-600/10 border border-yellow-600/30 text-yellow-400 font-black py-3.5 rounded-2xl
                               flex items-center justify-center gap-2 text-xs uppercase tracking-wide transition-all
                               disabled:opacity-40 active:scale-[0.98]">
                        <AlertTriangle size={16} /> Reportar
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>


<!-- ── VISTA DESKTOP (md+) ── -->
<div class="hidden md:flex flex-col h-full overflow-hidden">

    <!-- Sub-header -->
    <div class="px-8 py-3 border-b border-slate-800 flex items-center justify-between bg-[#0D1117]/60 shrink-0">
        <div>
            <h2 class="text-white font-black text-base">Puerta Norte — Carril 1</h2>
            <div class="flex items-center gap-1.5 mt-0.5">
                <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                <span class="text-[10px] text-green-400 font-bold uppercase">Sistema en Línea</span>
            </div>
        </div>
        <p class="text-white font-mono font-bold text-lg">{new Date().toLocaleTimeString('es-MX')}</p>
    </div>

    <div class="flex flex-1 overflow-hidden gap-6 p-6">

        <!-- Cámara desktop -->
        <div class="flex flex-col gap-4 w-[58%] shrink-0">
            <div>
                <h3 class="text-white font-black text-xl">REGISTRO DE ENTRADA</h3>
                <p class="text-xs text-slate-500 mt-0.5">Escaneo automático de vehículos de carga</p>
            </div>

            <div class="relative flex-1 min-h-0 bg-[#12161B] rounded-xl overflow-hidden border border-slate-800 shadow-xl">
                <div class="absolute top-3 left-3 z-10 flex items-center gap-2 bg-black/60 px-3 py-1.5 rounded-lg border border-slate-700/50">
                    <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                    <span class="text-[10px] font-black tracking-widest text-slate-300">CAM-04 FEED LIVE</span>
                </div>
                <video bind:this={videoElDesktop} autoplay playsinline muted class="w-full h-full object-cover"></video>
                <div class="absolute inset-6 pointer-events-none">
                    <div class="absolute top-0 left-0 w-6 h-6 border-t-4 border-l-4 border-orange-500 rounded-tl"></div>
                    <div class="absolute top-0 right-0 w-6 h-6 border-t-4 border-r-4 border-orange-500 rounded-tr"></div>
                    <div class="absolute bottom-0 left-0 w-6 h-6 border-b-4 border-l-4 border-orange-500 rounded-bl"></div>
                    <div class="absolute bottom-0 right-0 w-6 h-6 border-b-4 border-r-4 border-orange-500 rounded-br"></div>
                </div>
                {#if scanning}
                    <div class="absolute inset-0 bg-black/50 flex flex-col items-center justify-center gap-3">
                        <div class="w-10 h-10 border-4 border-orange-500/30 border-t-orange-500 rounded-full animate-spin"></div>
                        <p class="text-orange-500 font-black uppercase tracking-widest text-sm animate-pulse">Analizando placa...</p>
                    </div>
                {/if}
            </div>

            <div class="flex gap-3 shrink-0">
                <button onclick={capturar} disabled={scanning}
                    class="flex-1 bg-orange-500 hover:bg-orange-600 active:scale-[0.98] disabled:opacity-50
                           text-black font-black py-3.5 rounded-xl flex items-center justify-center gap-2
                           uppercase tracking-widest text-sm shadow-lg shadow-orange-500/20 transition-all">
                    <Camera size={20} /> {scanning ? 'Procesando...' : 'Captura Rápida'}
                </button>
            </div>
        </div>

        <!-- Panel datos desktop -->
        <div class="flex flex-col gap-4 flex-1 overflow-y-auto custom-scrollbar">

            <div class="bg-[#1A1F26] rounded-xl border border-slate-800 overflow-hidden">
                <div class="flex items-center justify-between px-5 py-4 border-b border-slate-800">
                    <h4 class="font-black uppercase tracking-widest text-sm text-white">Datos Detectados</h4>
                    {#if scanResult}
                        <span class="text-[10px] font-bold px-2.5 py-1 rounded-full border {confBg(scanResult.confianza)} {confColor(scanResult.confianza)}">
                            Confianza {confLabel(scanResult.confianza)} · {scanResult.confianza}%
                        </span>
                    {:else}
                        <span class="text-[10px] font-bold px-2.5 py-1 rounded-full bg-slate-800 text-slate-500 border border-slate-700">Esperando escaneo</span>
                    {/if}
                </div>
                <div class="p-5 space-y-4">
                    <div>
                        <label class="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1.5">Placa Detectada</label>
                        <div class="flex items-center gap-2">
                            {#if editingPlaca}
                                <input bind:value={placa} onblur={() => editingPlaca = false} autofocus
                                    class="flex-1 bg-[#0D1117] border border-orange-500 rounded-lg px-4 py-2.5 text-lg font-black text-white tracking-widest focus:outline-none uppercase" />
                            {:else}
                                <div class="flex-1 bg-[#0D1117] border {scanResult ? 'border-slate-700' : 'border-slate-800'} rounded-lg px-4 py-2.5 flex items-center justify-between">
                                    <span class="text-lg font-black tracking-widest {placa ? 'text-white' : 'text-slate-700'}">{placa || '— — —'}</span>
                                    {#if placa && placa !== 'NO DETECTADA'}<Check size={18} class="text-green-500" />{/if}
                                </div>
                            {/if}
                            {#if scanResult}
                                <button onclick={() => editingPlaca = !editingPlaca} class="p-2.5 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
                                    <Edit3 size={16} class="text-slate-400" />
                                </button>
                            {/if}
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1.5">Empresa</label>
                            <input bind:value={empresa} placeholder="Nombre empresa" disabled={!scanResult}
                                class="w-full bg-[#0D1117] border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-orange-500 transition-colors disabled:opacity-40" />
                        </div>
                        <div>
                            <label class="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1.5">Tipo</label>
                            <input bind:value={tipoUnidad} disabled={!scanResult}
                                class="w-full bg-[#0D1117] border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-orange-500 transition-colors disabled:opacity-40" />
                        </div>
                    </div>
                    <div>
                        <label class="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1.5">Conductor</label>
                        <input bind:value={conductor} placeholder="Nombre del conductor" disabled={!scanResult}
                            class="w-full bg-[#0D1117] border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-orange-500 transition-colors disabled:opacity-40" />
                    </div>
                </div>
            </div>

            <div class="bg-[#1A1F26] rounded-xl border border-slate-800 p-5 space-y-3">
                <h4 class="font-black uppercase tracking-widest text-sm text-white">Inspección Visual</h4>
                <div class="grid grid-cols-2 gap-2">
                    <button onclick={() => danosVis = !danosVis} disabled={!scanResult}
                        class="flex items-center gap-2 p-3 rounded-lg border {danosVis ? 'border-red-500/40 bg-red-500/5' : 'border-slate-800 bg-[#12161B]'} transition-all disabled:opacity-40">
                        {#if danosVis}<CheckSquare size={16} class="text-red-500 shrink-0" />{:else}<Square size={16} class="text-slate-600 shrink-0" />{/if}
                        <span class="text-sm font-bold {danosVis ? 'text-red-400' : 'text-slate-400'}">Daños Visibles</span>
                    </button>
                    <button onclick={() => sellosRot = !sellosRot} disabled={!scanResult}
                        class="flex items-center gap-2 p-3 rounded-lg border {sellosRot ? 'border-red-500/40 bg-red-500/5' : 'border-slate-800 bg-[#12161B]'} transition-all disabled:opacity-40">
                        {#if sellosRot}<CheckSquare size={16} class="text-red-500 shrink-0" />{:else}<Square size={16} class="text-slate-600 shrink-0" />{/if}
                        <span class="text-sm font-bold {sellosRot ? 'text-red-400' : 'text-slate-400'}">Sellos Rotos</span>
                    </button>
                </div>
            </div>

            {#if actionMsg}
                <div class="px-4 py-3 rounded-xl border font-bold text-sm text-center
                    {actionType === 'ok' ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}">
                    {actionMsg}
                </div>
            {/if}

            <div class="space-y-3 pb-2">
                <button onclick={() => guardarRegistro('entrada')} disabled={!scanResult || saving}
                    class="w-full bg-orange-500 hover:bg-orange-600 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed
                           text-black font-black py-4 rounded-xl flex items-center justify-center gap-2 uppercase tracking-widest text-sm
                           shadow-lg shadow-orange-500/20 transition-all">
                    <ShieldCheck size={22} /> Autorizar Acceso
                </button>
                <div class="grid grid-cols-2 gap-3">
                    <button onclick={() => guardarRegistro('denegado')} disabled={!scanResult || saving}
                        class="bg-red-600/20 hover:bg-red-600/30 border border-red-600/40 text-red-400 font-black py-3 rounded-xl
                               flex items-center justify-center gap-2 uppercase tracking-wider text-xs transition-all disabled:opacity-40">
                        <ShieldX size={18} /> Denegar
                    </button>
                    <button onclick={() => guardarRegistro('denegado')} disabled={!scanResult || saving}
                        class="bg-yellow-600/10 hover:bg-yellow-600/20 border border-yellow-600/30 text-yellow-400 font-black py-3 rounded-xl
                               flex items-center justify-center gap-2 uppercase tracking-wider text-xs transition-all disabled:opacity-40">
                        <AlertTriangle size={18} /> Reportar
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<canvas bind:this={canvasEl} class="hidden"></canvas>

<style>
    .scanline {
        animation: scanline 2.5s ease-in-out infinite;
        top: 0;
    }
    @keyframes scanline {
        0%   { top: 0%;   opacity: 0.8; }
        50%  { top: 95%;  opacity: 1;   }
        100% { top: 0%;   opacity: 0.8; }
    }
</style>
