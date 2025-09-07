<script>
	import { createEventDispatcher, onMount } from 'svelte';

	export let connected = false;

	const dispatch = createEventDispatcher();

	let isListening = false;
	let isProcessing = false;
	let recognition = null;
	let speechSupported = false;
	let voiceEnabled = false;
	let lastTranscript = '';

	// Voice settings
	let voiceStatus = {
		voice_enabled: false,
		voice_available: false,
		voices_count: 0,
	};

	onMount(() => {
		checkVoiceSupport();
		checkBackendVoiceStatus();
	});

	function checkVoiceSupport() {
		speechSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;

		if (speechSupported) {
			const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
			recognition = new SpeechRecognition();

			recognition.continuous = false;
			recognition.interimResults = false;
			recognition.lang = 'en-US';

			recognition.onstart = () => {
				isListening = true;
				console.log('Voice recognition started');
			};

			recognition.onresult = (event) => {
				const transcript = event.results[0][0].transcript;
				lastTranscript = transcript;
				console.log('Voice input:', transcript);

				// Dispatch the voice input as a signal
				dispatch('voiceSignal', { text: transcript });
			};

			recognition.onerror = (event) => {
				console.error('Voice recognition error:', event.error);
				isListening = false;
				isProcessing = false;
			};

			recognition.onend = () => {
				isListening = false;
				isProcessing = false;
				console.log('Voice recognition ended');
			};
		}
	}

	async function checkBackendVoiceStatus() {
		try {
			const response = await fetch('/voice/status');
			if (response.ok) {
				voiceStatus = await response.json();
				voiceEnabled = voiceStatus.voice_enabled && voiceStatus.voice_available;
			}
		} catch (error) {
			console.error('Failed to check voice status:', error);
		}
	}

	function startVoiceInput() {
		if (!speechSupported || !recognition || isListening) return;

		try {
			isProcessing = true;
			recognition.start();
		} catch (error) {
			console.error('Failed to start voice recognition:', error);
			isProcessing = false;
		}
	}

	function stopVoiceInput() {
		if (recognition && isListening) {
			recognition.stop();
		}
	}

	async function playTextAsVoice(text) {
		if (!voiceEnabled || !text.trim()) return;

		try {
			const response = await fetch(`/voice/tts?text=${encodeURIComponent(text)}`);

			if (response.ok) {
				const audioBlob = await response.blob();
				const audioUrl = URL.createObjectURL(audioBlob);
				const audio = new Audio(audioUrl);

				audio.onended = () => {
					URL.revokeObjectURL(audioUrl);
				};

				await audio.play();
				console.log('Playing voice for:', text);
			} else {
				console.error('Voice synthesis failed:', response.status);
			}
		} catch (error) {
			console.error('Voice playback error:', error);
		}
	}

	// Expose the playTextAsVoice function for parent components
	export { playTextAsVoice };
</script>

<div class="voice-controls">
	{#if speechSupported}
		<button
			class="voice-btn"
			class:listening={isListening}
			class:processing={isProcessing}
			disabled={!connected || isProcessing}
			on:click={startVoiceInput}
			title="Voice input (speak your signal)"
		>
			{#if isListening}
				🎤
			{:else if isProcessing}
				⏳
			{:else}
				🎙️
			{/if}
		</button>
	{:else}
		<button class="voice-btn disabled" disabled title="Voice input not supported in this browser">
			🚫
		</button>
	{/if}

	{#if voiceEnabled}
		<div class="voice-status">
			<span class="voice-indicator enabled" title="Voice output enabled">🔊</span>
		</div>
	{:else}
		<div class="voice-status">
			<span class="voice-indicator disabled" title="Voice output not available">🔇</span>
		</div>
	{/if}

	{#if lastTranscript}
		<div class="last-transcript">
			Last: "{lastTranscript}"
		</div>
	{/if}
</div>

<style>
	.voice-controls {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 15px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		margin: 0.5rem 0;
	}

	.voice-btn {
		background: linear-gradient(135deg, #667eea, #764ba2);
		border: none;
		color: white;
		width: 40px;
		height: 40px;
		border-radius: 50%;
		font-size: 1.2rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
	}

	.voice-btn:hover:not(:disabled) {
		transform: scale(1.1);
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
	}

	.voice-btn:active:not(:disabled) {
		transform: scale(0.95);
	}

	.voice-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none !important;
	}

	.voice-btn.listening {
		background: linear-gradient(135deg, #ff6b6b, #ee5a24);
		animation: pulse 1.5s ease-in-out infinite;
	}

	.voice-btn.processing {
		background: linear-gradient(135deg, #feca57, #ff9ff3);
		animation: spin 1s linear infinite;
	}

	.voice-btn.disabled {
		background: #666;
		color: #999;
	}

	.voice-status {
		display: flex;
		align-items: center;
		font-size: 0.9rem;
	}

	.voice-indicator {
		font-size: 1rem;
	}

	.voice-indicator.enabled {
		color: #90ee90;
	}

	.voice-indicator.disabled {
		color: #ffb3b3;
	}

	.last-transcript {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		max-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	@keyframes pulse {
		0%,
		100% {
			transform: scale(1);
			opacity: 1;
		}
		50% {
			transform: scale(1.05);
			opacity: 0.8;
		}
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 600px) {
		.voice-controls {
			flex-wrap: wrap;
			gap: 0.25rem;
		}

		.last-transcript {
			width: 100%;
			text-align: center;
		}
	}
</style>
