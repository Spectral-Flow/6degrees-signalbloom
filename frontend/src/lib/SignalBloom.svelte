<script>
	import { onMount } from 'svelte';
	import Signal from './Signal.svelte';
	import SignalInput from './SignalInput.svelte';
	import VoiceControls from './VoiceControls.svelte';
	import InnovationTree from './InnovationTree.svelte';
	
	let websocket;
	let connected = false;
	let signals = [];
	let connectionStatus = 'Connecting...';
	let reconnectAttempts = 0;
	let maxReconnectAttempts = 5;
	let reconnectTimeout;
	let voiceControlsRef;

	// Innovation tree state
	let showInnovationTree = false;
	let selectedInnovationObject = null;

	// WebSocket connection management with improved error handling
	function connectWebSocket() {
		try {
			// Clear any existing timeout
			if (reconnectTimeout) {
				clearTimeout(reconnectTimeout);
			}

			const wsUrl = getWebSocketUrl();
			websocket = new WebSocket(wsUrl);
			
			websocket.onopen = () => {
				connected = true;
				connectionStatus = 'Connected to Signal Bloom';
				reconnectAttempts = 0; // Reset counter on successful connection
				console.log('WebSocket connected successfully');
			};
			
			websocket.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);
					
					if (data.type === 'signal') {
						// Add new signal to the front of the array for latest-first display
						signals = [data, ...signals];
						
						// Limit stored signals to prevent memory issues
						if (signals.length > 100) {
							signals = signals.slice(0, 100);
						}
						
						// Auto-play voice for new signals (optional feature)
						if (voiceControlsRef && data.text) {
							setTimeout(() => {
								voiceControlsRef.playTextAsVoice(data.text);
							}, 500); // Small delay to avoid overlapping voices
						}
					} else if (data.type === 'error') {
						console.error('Server error:', data.message);
						connectionStatus = `Server error: ${data.message}`;
					}
				} catch (error) {
					console.error('Error parsing WebSocket message:', error);
				}
			};
			
			websocket.onclose = (event) => {
				connected = false;
				
				if (event.wasClean) {
					connectionStatus = 'Disconnected';
					console.log('WebSocket closed cleanly');
				} else {
					connectionStatus = 'Connection lost';
					console.warn('WebSocket closed unexpectedly:', event.code, event.reason);
					attemptReconnection();
				}
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
			attemptReconnection();
		}
	}

	function getWebSocketUrl() {
		// Determine WebSocket URL based on current location
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const host = window.location.hostname;
		const port = process.env.NODE_ENV === 'development' ? '8000' : window.location.port;
		return `${protocol}//${host}:${port}/ws`;
	}

	function attemptReconnection() {
		if (reconnectAttempts < maxReconnectAttempts) {
			const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000); // Exponential backoff
			reconnectAttempts++;
			
			connectionStatus = `Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`;
			
			reconnectTimeout = setTimeout(() => {
				connectWebSocket();
			}, delay);
		} else {
			connectionStatus = 'Connection failed - Please refresh the page';
		}
	}

	function resetConnection() {
		reconnectAttempts = 0;
		connectWebSocket();
	}
	
	// Send signal to backend with error handling
	function sendSignal(text) {
		if (websocket && connected && websocket.readyState === WebSocket.OPEN) {
			try {
				const signal = {
					type: 'signal',
					text: text.trim(),
					x: Math.random() * 90 + 5, // 5-95% to keep signals within bounds
					y: Math.random() * 90 + 5
				};
				websocket.send(JSON.stringify(signal));
			} catch (error) {
				console.error('Error sending signal:', error);
				connectionStatus = 'Send failed - reconnecting...';
				attemptReconnection();
			}
		} else {
			console.warn('Cannot send signal: WebSocket not connected');
		}
	}
	
	function handleInnovationTreeOpen(event) {
		const { objectId } = event.detail;
		selectedInnovationObject = objectId;
		showInnovationTree = true;
	}
	
	function handleInnovationTreeClose() {
		showInnovationTree = false;
		selectedInnovationObject = null;
	}
	
	onMount(() => {
		connectWebSocket();
		
		// Cleanup on component destroy
		return () => {
			if (reconnectTimeout) {
				clearTimeout(reconnectTimeout);
			}
			if (websocket) {
				websocket.close(1000, 'Component unmounting');
			}
		};
	});
</script>

<main class="bloom-container">
	<header class="bloom-header">
		<h1>🌸 Signal Bloom</h1>
		<p class="subtitle">A living garden of shared sparks</p>
		<div class="status-container">
			<div class="status" class:connected class:disconnected={!connected}>
				{connectionStatus}
			</div>
			{#if !connected && reconnectAttempts >= maxReconnectAttempts}
				<button class="reconnect-btn" on:click={resetConnection}>
					↻ Reconnect
				</button>
			{/if}
		</div>
	</header>
	
	<SignalInput {connected} on:signal={(e) => sendSignal(e.detail.text)} />
	
	<VoiceControls 
		bind:this={voiceControlsRef}
		{connected} 
		on:voiceSignal={(e) => sendSignal(e.detail.text)} 
	/>
	
	<div class="bloom-garden">
		{#each signals as signal (signal.id)}
			<Signal {signal} on:openInnovationTree={handleInnovationTreeOpen} />
		{/each}
		
		{#if signals.length === 0}
			<div class="empty-garden">
				<p>🌱</p>
				<p>Your garden awaits the first bloom...</p>
			</div>
		{/if}
	</div>
</main>

<!-- Innovation Tree Modal -->
<InnovationTree 
	objectId={selectedInnovationObject}
	visible={showInnovationTree}
	on:close={handleInnovationTreeClose}
/>

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
	
	.status-container {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
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
	
	.reconnect-btn {
		background: linear-gradient(135deg, #667eea, #764ba2);
		border: none;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.3s ease;
		box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
	}
	
	.reconnect-btn:hover {
		transform: translateY(-1px);
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
	}
	
	.reconnect-btn:active {
		transform: translateY(0);
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