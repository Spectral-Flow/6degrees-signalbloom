<script>
	export let signal;
	
	import { onMount } from 'svelte';
	
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
	
	// Calculate position based on signal coordinates
	$: style = `
		left: ${signal.x}%; 
		top: ${signal.y}%;
	`;
</script>

<div 
	class="signal" 
	bind:this={element}
	{style}
	title="{signal.text} - {new Date(signal.timestamp).toLocaleTimeString()}"
>
	<div class="signal-core">
		<div class="signal-text">{signal.text}</div>
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