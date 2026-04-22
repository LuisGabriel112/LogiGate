<script>
    import { Truck, Contact, Lock, LogIn, Fingerprint, Globe, Eye, EyeOff } from 'lucide-svelte';
    import { onMount } from 'svelte';

    let loading = $state(false);
    let showPassword = $state(false);
    let usuario = $state('');
    let password = $state('');

    const handleLogin = async (e) => {
        e.preventDefault();
        loading = true;
        await new Promise(r => setTimeout(r, 800));
        window.location.href = '/panel-control';
    };
</script>

<div class="min-h-screen bg-[#080A0E] flex flex-col items-center justify-center p-4 font-sans text-slate-300 relative overflow-hidden">

    <!-- Fondo animado: grid + glow -->
    <div class="absolute inset-0 bg-[linear-gradient(rgba(255,140,0,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,140,0,0.03)_1px,transparent_1px)] bg-[size:48px_48px]"></div>
    <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-orange-500/5 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-0 left-1/4 w-96 h-96 bg-orange-600/4 rounded-full blur-3xl pointer-events-none"></div>

    <!-- Card -->
    <div class="w-full max-w-sm relative z-10">
        <!-- Borde superior con degradado -->
        <div class="h-px w-full bg-gradient-to-r from-transparent via-orange-500 to-transparent mb-px"></div>
        <div class="bg-[#111418]/90 backdrop-blur-xl rounded-xl overflow-hidden shadow-2xl shadow-black/60 border border-slate-800/60">

            <!-- Header -->
            <div class="pt-10 pb-7 flex flex-col items-center px-8">
                <div class="flex items-center gap-3 mb-2">
                    <div class="p-2 bg-orange-500/10 rounded-xl border border-orange-500/20">
                        <Truck class="text-orange-500" size={28} strokeWidth={2} />
                    </div>
                    <h1 class="text-3xl font-black text-white tracking-tight">
                        Logi<span class="text-orange-500">Gate</span>
                    </h1>
                </div>
                <p class="text-[10px] uppercase tracking-[0.35em] font-bold text-slate-600">Gestión de patios · AI</p>
            </div>

            <!-- Form -->
            <form onsubmit={handleLogin} class="px-8 pb-8 space-y-5">

                <div class="space-y-1.5">
                    <label for="usuario" class="text-[10px] font-black uppercase tracking-widest text-slate-500 block">Usuario</label>
                    <div class="relative group">
                        <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-600 group-focus-within:text-orange-500 transition-colors">
                            <Contact size={16} />
                        </span>
                        <input
                            id="usuario"
                            bind:value={usuario}
                            type="text"
                            placeholder="ID de Empleado"
                            class="w-full bg-[#0D1117] border border-slate-800 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500/50 transition-all placeholder:text-slate-700 text-slate-200 hover:border-slate-700"
                        />
                    </div>
                </div>

                <div class="space-y-1.5">
                    <label for="password" class="text-[10px] font-black uppercase tracking-widest text-slate-500 block">Contraseña</label>
                    <div class="relative group">
                        <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-600 group-focus-within:text-orange-500 transition-colors">
                            <Lock size={16} />
                        </span>
                        <input
                            id="password"
                            bind:value={password}
                            type={showPassword ? 'text' : 'password'}
                            placeholder="••••••••"
                            class="w-full bg-[#0D1117] border border-slate-800 rounded-lg py-3 pl-10 pr-10 text-sm focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500/50 transition-all placeholder:text-slate-700 text-slate-200 hover:border-slate-700"
                        />
                        <button
                            type="button"
                            onclick={() => showPassword = !showPassword}
                            class="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-600 hover:text-slate-400 transition-colors"
                        >
                            {#if showPassword}
                                <EyeOff size={16} />
                            {:else}
                                <Eye size={16} />
                            {/if}
                        </button>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    class="w-full relative overflow-hidden bg-orange-500 hover:bg-orange-400 active:scale-[0.98] disabled:opacity-80 transition-all text-black font-black py-3.5 rounded-lg flex items-center justify-center gap-2.5 uppercase tracking-[0.12em] text-sm shadow-lg shadow-orange-500/25 mt-2"
                >
                    {#if loading}
                        <div class="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
                        <span>Verificando...</span>
                    {:else}
                        <LogIn size={18} />
                        <span>Iniciar Sesión</span>
                    {/if}
                </button>

                <div class="text-center">
                    <button type="button" class="text-[11px] text-slate-600 hover:text-orange-500 transition-colors">¿Olvidó su contraseña?</button>
                </div>

                <div class="relative py-1">
                    <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-slate-800"></div></div>
                    <div class="relative flex justify-center text-[9px] uppercase tracking-[0.25em] font-black text-slate-700">
                        <span class="bg-[#111418] px-3">o continúa con</span>
                    </div>
                </div>

                <button
                    type="button"
                    class="w-full flex items-center justify-center gap-2.5 text-[11px] font-bold text-slate-500 hover:text-orange-400 transition-colors py-2.5 rounded-lg border border-slate-800 hover:border-orange-500/30 hover:bg-orange-500/5"
                >
                    <Fingerprint size={18} class="text-orange-500/70" /> Acceso Biométrico
                </button>
            </form>
        </div>

        <!-- Footer -->
        <div class="mt-5 flex justify-between items-center px-1 opacity-40">
            <div class="flex items-center gap-1.5 text-[10px] font-bold">
                <Globe size={11} /> Español (MX)
            </div>
            <span class="text-[10px] font-mono text-slate-600">v2.4.1</span>
        </div>
    </div>
</div>
