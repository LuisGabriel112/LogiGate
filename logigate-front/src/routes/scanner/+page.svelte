<script>
    import { onMount } from 'svelte';
    import { Scan, CheckCircle, XCircle, RotateCcw, Upload, ImagePlus, Zap, Shield, ShieldOff } from 'lucide-svelte';

    const API = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000';

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

    onMount(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            videoSource.srcObject = stream;
        } catch (err) {
            error = "No se pudo acceder a la cámara.";
        }
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
        isScanning = true;
        resultado = null;
        error = null;
        startScanLine();
        sendToBackend(capturedImage);
    };

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        capturedImage = URL.createObjectURL(file);
        isScanning = true;
        resultado = null;
        error = null;
        startScanLine();
        sendFileToBackend(file);
    };

    const sendToBackend = async (base64) => {
        try {
            const res = await fetch(base64);
            const blob = await res.blob();
            const fd = new FormData();
            fd.append('image', blob, 'captura.jpg');
            const r = await fetch(`${API}/api/v1/scan`, { method: 'POST', body: fd });
            if (!r.ok) throw new Error(`Error ${r.status}`);
            resultado = await r.json();
        } catch (err) {
            error = "No se pudo conectar con el servidor de IA.";
        } finally {
            isScanning = false;
            stopScanLine();
        }
    };

    const sendFileToBackend = async (file) => {
        try {
            const fd = new FormData();
            fd.append('image', file, file.name);
            const r = await fetch(`${API}/api/v1/scan`, { method: 'POST', body: fd });
            if (!r.ok) throw new Error(`Error ${r.status}`);
            resultado = await r.json();
        } catch (err) {
            error = "No se pudo conectar con el servidor de IA.";
        } finally {
            isScanning = false;
            stopScanLine();
        }
    };

    const resetear = () => {
        resultado = null;
        capturedImage = null;
        error = null;
        isScanning = false;
        stopScanLine();
        if (fileInput) fileInput.value = '';
    };

    const esAutorizado = $derived(resultado && !resultado.status?.toLowerCase().includes('denegad') && !resultado.status?.toLowerCase().includes('error'));
    const confPct = $derived(resultado ? Math.round(resultado.confidence * 100) : 0);
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

            <!-- Overlay oscuro en bordes -->
            <div class="absolute inset-0 pointer-events-none">
                <div class="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/30"></div>

                <!-- Marco de enfoque -->
                <div class="absolute inset-8 border border-orange-500/30 rounded-lg">
                    <!-- Esquinas -->
                    <div class="absolute top-0 left-0 w-5 h-5 border-t-2 border-l-2 border-orange-500 rounded-tl-sm"></div>
                    <div class="absolute top-0 right-0 w-5 h-5 border-t-2 border-r-2 border-orange-500 rounded-tr-sm"></div>
                    <div class="absolute bottom-0 left-0 w-5 h-5 border-b-2 border-l-2 border-orange-500 rounded-bl-sm"></div>
                    <div class="absolute bottom-0 right-0 w-5 h-5 border-b-2 border-r-2 border-orange-500 rounded-br-sm"></div>
                </div>

                <!-- Línea de escaneo animada -->
                {#if isScanning}
                    <div
                        class="absolute left-8 right-8 h-px bg-gradient-to-r from-transparent via-orange-500 to-transparent shadow-[0_0_8px_2px_rgba(249,115,22,0.6)] transition-none"
                        style="top: calc(2rem + {scanLinePos}%)"
                    ></div>
                {/if}

                <!-- Label -->
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
                <!-- Barra de progreso fake -->
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
                onclick={() => fileInput.click()}
                class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all text-slate-300 font-bold py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
            >
                <ImagePlus size={16} /> Cambiar imagen
            </button>
        {/if}

        <!-- Resultado -->
        {#if resultado}
            <div class="bg-[#0E1015] rounded-2xl border {esAutorizado ? 'border-green-500/30' : 'border-red-500/30'} overflow-hidden shadow-2xl">

                <!-- Imagen capturada -->
                {#if resultado.image_url}
                    <div class="relative">
                        <img src="{API}{resultado.image_url}" alt="Placa capturada" class="w-full object-cover max-h-40" />
                        <div class="absolute inset-0 bg-gradient-to-t from-[#0E1015] to-transparent"></div>
                    </div>
                {/if}

                <div class="p-5 space-y-4">
                    <!-- Encabezado resultado -->
                    <div class="flex items-center gap-3">
                        <div class="p-2.5 {esAutorizado ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'} rounded-xl border">
                            {#if esAutorizado}
                                <Shield size={22} class="text-green-400" />
                            {:else}
                                <ShieldOff size={22} class="text-red-400" />
                            {/if}
                        </div>
                        <div>
                            <p class="text-[10px] uppercase tracking-widest text-slate-500 font-black">Placa Detectada</p>
                            <p class="text-2xl font-black text-white tracking-[0.15em]">{resultado.plate}</p>
                        </div>
                        <div class="ml-auto">
                            <span class="text-[10px] font-black px-2.5 py-1 rounded-full border {esAutorizado ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}">
                                {esAutorizado ? 'AUTORIZADO' : 'DENEGADO'}
                            </span>
                        </div>
                    </div>

                    <!-- Métricas -->
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
</div>

<style>
    @keyframes scan {
        0%   { width: 0%; margin-left: 0; }
        50%  { width: 100%; margin-left: 0; }
        100% { width: 0%; margin-left: 100%; }
    }
</style>
