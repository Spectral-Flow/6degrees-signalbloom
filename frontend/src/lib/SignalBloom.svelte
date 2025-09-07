<script>
	import { onMount } from 'svelte';
	import Signal from './Signal.svelte';
	import SignalInput from './SignalInput.svelte';
	
	let websocket;
	let connected = false;
	let signals = [];
	let connectionStatus = 'Connecting...';

	// WebSocket connection management
	function connectWebSocket() {
		try {
			websocket = new WebSocket('ws://localhost:8000/ws');
			
			websocket.onopen = () => {
				connected = true;
				connectionStatus = 'Connected to Signal Bloom';
			};
			
			websocket.onmessage = (event) => {
				const data = JSON.parse(event.data);
				if (data.type === 'signal') {
					// Add new signal to the front of the array for latest-first display
					signals = [data, ...signals];
				}
			};
			
			websocket.onclose = () => {
				connected = false;
				connectionStatus = 'Disconnected';
				// Attempt reconnection after 3 seconds
				setTimeout(() => {
					connectionStatus = 'Reconnecting...';
					connectWebSocket();
				}, 3000);
			};
			
			websocket.onerror = (error) => {
				console.error('WebSocket error:', error);
				connected = false;
				connectionStatus = 'Connection error';
			};
		} catch (error) {
			console.error('Failed to create WebSocket:', error);
			connected = false;
			connectionStatus = 'Connection failed';
		}
	}
	
	// Send signal to backend
	function sendSignal(text) {
		if (websocket && connected) {
			const signal = {
				type: 'signal',
				text: text,
				x: Math.random() * 90 + 5, // 5-95% to keep signals within bounds
				y: Math.random() * 90 + 5
			};
			websocket.send(JSON.stringify(signal));
		}
	}
	
	onMount(() => {
		connectWebSocket();
		
		// Cleanup on component destroy
		return () => {
			if (websocket) {
				websocket.close();
			}
		};
	});
</script>

<main class="bloom-container">
	<header class="bloom-header">
		<h1>🌸 Signal Bloom</h1>
		<p class="subtitle">A living garden of shared sparks</p>
		<div class="status" class:connected class:disconnected={!connected}>
			{connectionStatus}
		</div>
	</header>
	
	<SignalInput {connected} on:signal={(e) => sendSignal(e.detail.text)} />
	
	<div class="bloom-garden">
		{#each signals as signal (signal.id)}
			<Signal {signal} />
		{/each}
		
		{#if signals.length === 0}
			<div class="empty-garden">
				<p>🌱</p>
				<p>Your garden awaits the first bloom...</p>
			</div>
		{/if}
	</div>
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		min-height: 100vh;
		overflow-x: hidden;
	}
	
	.bloom-container {
		max-width: 100vw;
		height: 100vh;
		position: relative;
		overflow: hidden;
	}
	
	.bloom-header {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 100;
		background: rgba(0, 0, 0, 0.1);
		backdrop-filter: blur(10px);
		padding: 1rem 2rem;
		text-align: center;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.bloom-header h1 {
		margin: 0;
		font-size: 2.5rem;
		font-weight: 300;
		background: linear-gradient(45deg, #ff9a9e, #fecfef, #fecfef);
		background-size: 200% 200%;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: gradient-shift 3s ease infinite;
	}
	
	@keyframes gradient-shift {
		0%, 100% { background-position: 0% 50%; }
		50% { background-position: 100% 50%; }
	}
	
	.subtitle {
		margin: 0.5rem 0;
		opacity: 0.8;
		font-size: 1rem;
		font-weight: 300;
	}
	
	.status {
		font-size: 0.9rem;
		padding: 0.25rem 1rem;
		border-radius: 20px;
		display: inline-block;
		transition: all 0.3s ease;
	}
	
	.status.connected {
		background: rgba(0, 255, 0, 0.2);
		color: #90ee90;
	}
	
	.status.disconnected {
		background: rgba(255, 0, 0, 0.2);
		color: #ffb3b3;
	}
	
	.bloom-garden {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.bloom-garden .signal {
		pointer-events: all;
	}
	
	.empty-garden {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
		opacity: 0.6;
		font-size: 1.2rem;
		pointer-events: none;
	}
	
	.empty-garden p:first-child {
		font-size: 4rem;
		margin: 0;
		animation: gentle-pulse 2s ease-in-out infinite;
	}
	
	.empty-garden p:last-child {
		margin: 1rem 0 0 0;
		font-weight: 300;
	}
	
	@keyframes gentle-pulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 0.8; transform: scale(1.05); }
	}
</style>