<script>
    import { Truck, Contact, Lock, LogIn, Fingerprint, Globe } from 'lucide-svelte';
    import { onMount } from 'svelte';

    onMount(() => {
      const loginButton = document.getElementById('login-button');
      loginButton.addEventListener('click', () => {
        window.location.href = '/panel-control';
      });
    });

  </script>
  
  <div class="min-h-screen bg-[#0B0C10] flex flex-col items-center justify-center p-4 font-sans text-slate-300">
      
      <div class="w-full max-w-sm bg-[#1A1F26] rounded-xl overflow-hidden shadow-2xl border-t-4 border-orange-500">
          
          <div class="pt-10 pb-6 flex flex-col items-center">
              <div class="flex items-center gap-3 mb-1">
                  <Truck class="text-orange-500" size={36} strokeWidth={2.5} />
                  <h1 class="text-3xl font-bold text-white tracking-tight">LogiGate <span class="text-orange-500">AI</span></h1>
              </div>
              <p class="text-[10px] uppercase tracking-[0.3em] font-black text-slate-500">Gestión de patios inteligente</p>
          </div>
  
          <form class="px-8 pb-8 space-y-6">
              
              <div class="space-y-2">
                  <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 block ml-1">Usuario</label>
                  <div class="relative">
                      <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-teal-600/70">
                          <Contact size={18} />
                      </span>
                      <input
                          type="text"
                          placeholder="ID de Empleado"
                          class="w-full bg-[#0D1117] border border-slate-800 rounded-md py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-orange-500 transition-all placeholder:text-slate-700 text-teal-500"
                      />
                  </div>
              </div>
  
              <div class="space-y-2">
                  <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 block ml-1">Contraseña</label>
                  <div class="relative">
                      <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-teal-600/70">
                          <Lock size={18} />
                      </span>
                      <input
                          type="password"
                          placeholder="••••••••"
                          class="w-full bg-[#0D1117] border border-slate-800 rounded-md py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-orange-500 transition-all placeholder:text-slate-700 text-teal-500"
                      />
                  </div>
              </div>
  
              <button id="login-button" class="w-full bg-orange-500 hover:bg-orange-600 active:scale-[0.97] transition-all text-black font-black py-3.5 rounded-md flex items-center justify-center gap-3 uppercase tracking-[0.15em] text-sm shadow-lg shadow-orange-500/20">
                  <LogIn size={20} /> Iniciar Sesión
              </button>
  
              <div class="text-center">
                  <a href="#" class="text-[11px] text-slate-500 hover:text-slate-300 underline underline-offset-4 decoration-slate-700 transition-colors">¿Olvidó su contraseña?</a>
              </div>
  
              <div class="relative py-2">
                  <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-slate-800"></div></div>
                  <div class="relative flex justify-center text-[9px] uppercase tracking-[0.2em] font-black text-slate-600">
                      <span class="bg-[#1A1F26] px-3">Seguridad</span>
                  </div>
              </div>
  
              <button type="button" class="w-full flex items-center justify-center gap-2 text-[11px] font-bold text-slate-400 hover:text-white transition-colors py-2">
                  <Fingerprint size={20} class="text-orange-500" /> Acceso Biométrico
              </button>
          </form>
      </div>
  
      <div class="w-full max-w-sm mt-6 flex justify-between items-center px-2 opacity-40">
          <div class="flex items-center gap-2 text-[10px] font-bold">
              <Globe size={12} /> Español (ES)
          </div>
          <span class="text-[10px] font-mono">v2.4.0-stable</span>
      </div>
  </div>
  