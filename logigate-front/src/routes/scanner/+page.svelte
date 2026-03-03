<script>
    import { onMount } from 'svelte';
    import { Camera, Scan, CheckCircle } from 'lucide-svelte';
  
    let videoSource;
    let canvasElement;
    let isScanning = false;
    let capturedImage = null;
  
    // Iniciar cámara al cargar la página
    onMount(async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { facingMode: 'environment' } // Usa la cámara trasera en celulares
        });
        videoSource.srcObject = stream;
      } catch (err) {
        console.error("Error al acceder a la cámara:", err);
      }
    });
  
    const takeSnapshot = () => {
      const context = canvasElement.getContext('2d');
      canvasElement.width = videoSource.videoWidth;
      canvasElement.height = videoSource.videoHeight;
      context.drawImage(videoSource, 0, 0, canvasElement.width, canvasElement.height);
      
      // Convertir a Base64 para enviar al backend
      capturedImage = canvasElement.toDataURL('image/jpeg');
      isScanning = true;
      
      // Aquí llamarías a la función de Joshua: sendToBackend(capturedImage);
    };
  </script>
  
  <div class="min-h-screen bg-[#0B0C10] text-white p-6 flex flex-col items-center">
    <header class="w-full flex justify-between items-center mb-8">
      <h1 class="text-xl font-bold tracking-tighter text-orange-500 italic">LOGIGATE AI</h1>
      <div class="bg-slate-800 px-3 py-1 rounded-full text-xs">MODO: GUARDIA</div>
    </header>
  
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
  
    <canvas bind:this={canvasElement} class="hidden"></canvas>
  
    <div class="mt-8 w-full max-w-md">
      {#if !isScanning}
        <button 
          on:click={takeSnapshot}
          class="w-full bg-orange-500 hover:bg-orange-600 active:scale-95 transition-all text-black font-black py-4 rounded-xl flex justify-center items-center gap-2 uppercase tracking-widest"
        >
          <Scan size={24} /> Capturar Entrada
        </button>
      {:else}
        <div class="bg-slate-800 p-4 rounded-xl border border-orange-500 animate-pulse">
          <p class="text-center text-orange-500 font-bold uppercase text-sm">Procesando con IA...</p>
        </div>
      {/if}
    </div>
  </div>