<script>
	import { Truck, CheckCircle2, AlertTriangle, ArrowUpRight, MapPin } from 'lucide-svelte';
</script>

<div class="p-8 space-y-8">
	<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
		<div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800 relative overflow-hidden group">
			<div class="flex justify-between items-start mb-4">
				<div>
					<p class="text-xs font-black uppercase text-slate-500 tracking-widest">Unidades en Patio</p>
					<h3 class="text-4xl font-bold text-white mt-1">45 <span class="text-xl text-slate-500">/ 100</span></h3>
				</div>
				<div class="bg-slate-800/50 p-3 rounded-lg"><Truck class="text-orange-500" /></div>
			</div>
			<div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
				<div class="bg-orange-500 h-full w-[45%]"></div>
			</div>
			<p class="text-[10px] text-orange-500 mt-2 font-bold uppercase">Ocupación actual: 45%</p>
		</div>

		<div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800">
			<div class="flex justify-between items-start mb-4">
				<div>
					<p class="text-xs font-black uppercase text-slate-500 tracking-widest">Cajones Disponibles</p>
					<h3 class="text-4xl font-bold text-white mt-1">55</h3>
				</div>
				<div class="bg-slate-800/50 p-3 rounded-lg text-green-500"><CheckCircle2 /></div>
			</div>
			<div class="flex items-center gap-2">
				<span class="text-[10px] bg-green-500/10 text-green-500 px-2 py-1 rounded font-bold">+5 vs ayer</span>
				<p class="text-[10px] text-slate-500 uppercase font-bold">Capacidad media</p>
			</div>
		</div>

		<div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800">
			<div class="flex justify-between items-start mb-4">
				<div>
					<p class="text-xs font-black uppercase text-slate-500 tracking-widest">Estado del Patio</p>
					<h3 class="text-3xl font-bold text-white mt-1 italic">Operativo</h3>
				</div>
				<div class="bg-slate-800/50 p-3 rounded-lg text-orange-500"><ArrowUpRight /></div>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></div>
				<p class="text-[10px] text-orange-500 uppercase font-black tracking-widest">Alerta de Saturación</p>
			</div>
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
		<div class="lg:col-span-2 bg-[#1A1F26] p-6 rounded-xl border border-slate-800">
			<div class="flex justify-between items-center mb-8">
				<div>
					<h4 class="text-lg font-bold text-white">Predicción de Arribos (IA)</h4>
					<p class="text-[10px] text-slate-500 uppercase font-bold">Volumen de Arribo: Real vs Estimado</p>
				</div>
				<select class="bg-slate-800 border-none text-xs rounded-md text-white px-3 py-2 outline-none">
					<option>Hoy</option>
					<option>Mañana</option>
				</select>
			</div>
			<div class="h-64 w-full bg-[#12161B] rounded-lg flex items-center justify-center border border-slate-800/50 relative overflow-hidden">
				<svg class="absolute inset-0 w-full h-full" viewBox="0 0 400 100" preserveAspectRatio="none">
					<path d="M0 80 Q 100 20, 200 60 T 400 40" fill="none" stroke="#FF8C00" stroke-width="3" stroke-linecap="round" />
					<path d="M0 85 Q 100 30, 200 70 T 400 50" fill="none" stroke="#475569" stroke-width="2" stroke-dasharray="5,5" />
				</svg>
				<span class="text-slate-600 text-xs font-mono uppercase tracking-widest">Datos Procesados por JOLTEC AI</span>
			</div>
		</div>

		<div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800 flex flex-col">
			<div class="flex justify-between items-center mb-6">
				<h4 class="text-lg font-bold text-white">Actividad Reciente</h4>
				<button class="text-orange-500 text-[10px] font-bold uppercase hover:underline">Ver todo</button>
			</div>
			<div class="space-y-4 flex-grow overflow-y-auto">
				{#each ['ABC-123', 'XYZ-987', 'LMN-456', 'QWE-789'] as placa, i}
					<div class="flex items-center justify-between p-3 bg-[#12161B] rounded-lg border border-slate-800/50">
						<div class="flex items-center gap-3">
							<Truck size={16} class="text-slate-500" />
							<div>
								<p class="text-xs font-bold text-white">{placa}</p>
								<p class="text-[9px] text-slate-500">08:45 AM</p>
							</div>
						</div>
						<span class="text-[10px] px-2 py-1 rounded bg-orange-500/10 text-orange-500 font-bold italic">
							{i === 0 ? '2h 15m' : '30m'}
						</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>