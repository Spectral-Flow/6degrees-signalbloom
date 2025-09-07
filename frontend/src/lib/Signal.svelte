<script>
	export let signal;
	
	import { onMount, createEventDispatcher } from 'svelte';
	
	const dispatch = createEventDispatcher();
	
	let element;
	let mounted = false;
	
	onMount(() => {
		mounted = true;
		
		// Add a bloom animation delay based on when the signal was created
		const delay = Math.random() * 500; // Random delay up to 500ms
		setTimeout(() => {
			if (element) {
				element.classList.add('bloomed');
			}
		}, delay);
	});
	
	function handleClick() {
		if (signal.has_innovation_tree) {
			dispatch('openInnovationTree', {
				objectId: signal.innovation_object_id,
				signalText: signal.text
			});
		}
	}
	
	// Calculate position based on signal coordinates
	$: style = `
		left: ${signal.x}%; 
		top: ${signal.y}%;
	`;
	
	$: hasInnovationTree = signal.has_innovation_tree || false;
</script>

<div 
	class="signal" 
	class:innovation-enabled={hasInnovationTree}
	bind:this={element}
	{style}
	title="{signal.text} - {new Date(signal.timestamp).toLocaleTimeString()}{hasInnovationTree ? ' (Click to explore innovations)' : ''}"
	on:click={handleClick}
	on:keydown={(e) => e.key === 'Enter' && handleClick()}
	role={hasInnovationTree ? "button" : "presentation"}
	tabindex={hasInnovationTree ? "0" : "-1"}
>
	<div class="signal-core">
		<div class="signal-text">{signal.text}</div>
		{#if hasInnovationTree}
			<div class="innovation-indicator">🌳</div>
		{/if}
	</div>
	<div class="signal-rings">
		<div class="ring ring-1"></div>
		<div class="ring ring-2"></div>
		<div class="ring ring-3"></div>
	</div>
</div>

<style>
	.signal {
		position: absolute;
		transform: translate(-50%, -50%);
		cursor: pointer;
		z-index: 10;
		opacity: 0;
		transition: opacity 1s ease;
	}
	
	.signal:global(.bloomed) {
		opacity: 1;
	}
	
	.signal-core {
		position: relative;
		background: rgba(255, 255, 255, 0.9);
		color: #333;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.2);
		z-index: 2;
		transition: all 0.3s ease;
		animation: gentle-float 4s ease-in-out infinite;
	}
	
	.signal-text {
		font-size: 0.9rem;
		font-weight: 500;
		text-align: center;
		white-space: nowrap;
		max-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.signal-rings {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 1;
	}
	
	.ring {
		position: absolute;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		opacity: 0;
		animation: bloom-ripple 3s ease-out infinite;
	}
	
	.ring-1 {
		width: 60px;
		height: 60px;
		animation-delay: 0s;
	}
	
	.ring-2 {
		width: 80px;
		height: 80px;
		animation-delay: 1s;
	}
	
	.ring-3 {
		width: 100px;
		height: 100px;
		animation-delay: 2s;
	}
	
	.signal:hover .signal-core {
		transform: scale(1.1);
		box-shadow: 0 6px 30px rgba(0, 0, 0, 0.15);
		background: rgba(255, 255, 255, 0.95);
	}
	
	.signal:hover .ring {
		animation-play-state: paused;
		opacity: 0.6 !important;
	}
	
	/* Innovation-enabled signals */
	.signal.innovation-enabled {
		cursor: pointer;
	}
	
	.signal.innovation-enabled .signal-core {
		background: linear-gradient(135deg, rgba(255, 215, 0, 0.9), rgba(255, 255, 255, 0.9));
		border: 2px solid #ffd700;
		position: relative;
	}
	
	.signal.innovation-enabled:hover .signal-core {
		transform: scale(1.15);
		box-shadow: 0 8px 35px rgba(255, 215, 0, 0.4);
		background: linear-gradient(135deg, rgba(255, 215, 0, 1), rgba(255, 255, 255, 0.95));
	}
	
	.innovation-indicator {
		position: absolute;
		top: -8px;
		right: -8px;
		width: 20px;
		height: 20px;
		background: #ffd700;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 10px;
		border: 2px solid white;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
		animation: innovation-pulse 2s ease-in-out infinite;
	}
	
	@keyframes innovation-pulse {
		0%, 100% {
			transform: scale(1);
			opacity: 1;
		}
		50% {
			transform: scale(1.1);
			opacity: 0.8;
		}
	}
	
	@keyframes bloom-ripple {
		0% {
			transform: translate(-50%, -50%) scale(0);
			opacity: 0.8;
		}
		50% {
			opacity: 0.4;
		}
		100% {
			transform: translate(-50%, -50%) scale(2);
			opacity: 0;
		}
	}
	
	@keyframes gentle-float {
		0%, 100% {
			transform: translateY(0px);
		}
		50% {
			transform: translateY(-5px);
		}
	}
</style>