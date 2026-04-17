<script>
    import { onMount } from 'svelte';
    import { Scan, CheckCircle, XCircle, RotateCcw, Upload, ImagePlus } from 'lucide-svelte';

    const API = 'http://localhost:8000';

    let videoSource;
    let canvasElement;
    let fileInput;
    let isScanning = false;
    let capturedImage = null;
    let resultado = null;  // { plate, confidence, image_url, status }
    let error = null;
    let modo = 'camara'; // 'camara' | 'archivo'

    // Iniciar cámara al cargar la página
    onMount(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            videoSource.srcObject = stream;
        } catch (err) {
            console.error("Error al acceder a la cámara:", err);
            error = "No se pudo acceder a la cámara.";
        }
    });

    const takeSnapshot = () => {
        const context = canvasElement.getContext('2d');
        canvasElement.width = videoSource.videoWidth;
        canvasElement.height = videoSource.videoHeight;
        context.drawImage(videoSource, 0, 0, canvasElement.width, canvasElement.height);
        capturedImage = canvasElement.toDataURL('image/jpeg');
        isScanning = true;
        resultado = null;
        error = null;
        sendToBackend(capturedImage);
    };

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        capturedImage = URL.createObjectURL(file);
        isScanning = true;
        resultado = null;
        error = null;
        sendFileToBackend(file);
    };

    const sendToBackend = async (base64Image) => {
        try {
            const res = await fetch(base64Image);
            const blob = await res.blob();
            const formData = new FormData();
            formData.append('image', blob, 'captura.jpg');

            const response = await fetch(`${API}/api/v1/scan`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
            resultado = await response.json();
        } catch (err) {
            console.error("Error al procesar la imagen:", err);
            error = "No se pudo conectar con el servidor.";
        } finally {
            isScanning = false;
        }
    };

    const sendFileToBackend = async (file) => {
        try {
            const formData = new FormData();
            formData.append('image', file, file.name);

            const response = await fetch(`${API}/api/v1/scan`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
            resultado = await response.json();
        } catch (err) {
            console.error("Error al procesar la imagen:", err);
            error = "No se pudo conectar con el servidor.";
        } finally {
            isScanning = false;
        }
    };

    const resetear = () => {
        resultado = null;
        capturedImage = null;
        error = null;
        isScanning = false;
        if (fileInput) fileInput.value = '';
    };
</script>

<div class="min-h-screen bg-[#0B0C10] text-white p-6 flex flex-col items-center">
    <header class="w-full flex justify-between items-center mb-6">
        <h1 class="text-xl font-bold tracking-tighter text-orange-500 italic">LOGIGATE AI</h1>
        <div class="bg-slate-800 px-3 py-1 rounded-full text-xs">MODO: GUARDIA</div>
    </header>

    <!-- Selector de modo -->
    {#if !resultado && !isScanning}
        <div class="w-full max-w-md flex bg-slate-900 border border-slate-800 rounded-xl p-1 mb-6">
            <button
                on:click={() => { modo = 'camara'; resetear(); }}
                class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all
                    {modo === 'camara' ? 'bg-orange-500 text-black' : 'text-slate-500 hover:text-white'}"
            >
                <Scan size={14} /> Cámara
            </button>
            <button
                on:click={() => { modo = 'archivo'; resetear(); }}
                class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all
                    {modo === 'archivo' ? 'bg-orange-500 text-black' : 'text-slate-500 hover:text-white'}"
            >
                <ImagePlus size={14} /> Subir Foto
            </button>
        </div>
    {/if}

    <!-- Vista cámara -->
    {#if modo === 'camara' && !resultado}
        <div class="relative w-full max-w-md aspect-[3/4] bg-slate-900 rounded-2xl overflow-hidden border-2 border-slate-800 shadow-2xl">
            <video bind:this={videoSource} autoPlay playsInline class="w-full h-full object-cover"></video>

            <div class="absolute inset-0 border-[40px] border-black/40 pointer-events-none">
                <div class="w-full h-full border-2 border-orange-500/50 relative">
                    <div class="absolute top-0 left-0 w-4 h-4 border-t-4 border-l-4 border-orange-500"></div>
                    <div class="absolute top-0 right-0 w-4 h-4 border-t-4 border-r-4 border-orange-500"></div>
                    <div class="absolute bottom-0 left-0 w-4 h-4 border-b-4 border-l-4 border-orange-500"></div>
                    <div class="absolute bottom-0 right-0 w-4 h-4 border-b-4 border-r-4 border-orange-500"></div>
                </div>
            </div>
        </div>
    {/if}

    <!-- Vista subir archivo -->
    {#if modo === 'archivo' && !resultado && !isScanning}
        <div
            class="w-full max-w-md aspect-video bg-slate-900 rounded-2xl border-2 border-dashed border-slate-700 flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-orange-500 transition-colors"
            on:click={() => fileInput.click()}
            on:keydown={(e) => e.key === 'Enter' && fileInput.click()}
            role="button"
            tabindex="0"
        >
            {#if capturedImage}
                <img src={capturedImage} alt="Vista previa" class="w-full h-full object-contain rounded-2xl" />
            {:else}
                <Upload size={36} class="text-slate-600" />
                <p class="text-slate-500 text-sm font-bold uppercase tracking-widest">Toca para seleccionar foto</p>
                <p class="text-slate-600 text-xs">JPG, PNG, WEBP</p>
            {/if}
        </div>
    {/if}

    <canvas bind:this={canvasElement} class="hidden"></canvas>
    <input
        bind:this={fileInput}
        type="file"
        accept="image/*"
        class="hidden"
        on:change={handleFileUpload}
    />

    <div class="mt-6 w-full max-w-md space-y-4">

        <!-- Botón capturar (cámara) -->
        {#if modo === 'camara' && !isScanning && !resultado}
            <button
                on:click={takeSnapshot}
                class="w-full bg-orange-500 hover:bg-orange-600 active:scale-95 transition-all text-black font-black py-4 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest"
            >
                <Scan size={24} /> Capturar Entrada
            </button>
        {/if}

        <!-- Botón analizar (archivo) -->
        {#if modo === 'archivo' && !isScanning && !resultado && capturedImage}
            <button
                on:click={() => fileInput.click()}
                class="w-full bg-slate-700 hover:bg-slate-600 transition-all text-white font-black py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
            >
                <ImagePlus size={16} /> Cambiar imagen
            </button>
        {/if}

        <!-- Procesando -->
        {#if isScanning}
            <div class="bg-slate-800 p-4 rounded-xl border border-orange-500 animate-pulse">
                <p class="text-center text-orange-500 font-bold uppercase text-sm">Procesando con IA...</p>
            </div>
        {/if}

        <!-- Resultado -->
        {#if resultado}
            <div class="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
                {#if resultado.image_url}
                    <img src={resultado.image_url} alt="Placa capturada" class="w-full object-cover max-h-48" />
                {/if}

                <div class="p-5 space-y-4">
                    <div class="flex items-center gap-3">
                        <CheckCircle size={22} class="text-green-400 shrink-0" />
                        <div>
                            <p class="text-[10px] uppercase tracking-widest text-slate-500 font-black">Placa Detectada</p>
                            <p class="text-2xl font-black text-white tracking-widest">{resultado.plate}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-slate-900 rounded-xl p-3">
                            <p class="text-[10px] uppercase tracking-widest text-slate-500 font-black mb-1">Confianza IA</p>
                            <p class="text-lg font-black text-orange-500">{(resultado.confidence * 100).toFixed(1)}%</p>
                        </div>
                        <div class="bg-slate-900 rounded-xl p-3">
                            <p class="text-[10px] uppercase tracking-widest text-slate-500 font-black mb-1">Estado</p>
                            <p class="text-xs font-bold text-green-400">{resultado.status}</p>
                        </div>
                    </div>

                    <button
                        on:click={resetear}
                        class="w-full bg-slate-700 hover:bg-slate-600 transition-all text-white font-black py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
                    >
                        <RotateCcw size={16} /> Nueva Captura
                    </button>
                </div>
            </div>
        {/if}

        <!-- Error -->
        {#if error && !isScanning}
            <div class="bg-red-900/30 border border-red-500/50 rounded-xl p-4 flex items-center gap-3">
                <XCircle size={20} class="text-red-400 shrink-0" />
                <p class="text-sm text-red-300">{error}</p>
            </div>
            <button
                on:click={resetear}
                class="w-full bg-slate-700 hover:bg-slate-600 transition-all text-white font-black py-3 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest text-sm"
            >
                <RotateCcw size={16} /> Intentar de nuevo
            </button>
        {/if}

    </div>
</div>
