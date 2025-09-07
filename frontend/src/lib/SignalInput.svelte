<script>
	import { createEventDispatcher } from 'svelte';
	
	export let connected = false;
	
	const dispatch = createEventDispatcher();
	
	let signalText = '';
	let inputElement;
	
	function handleSubmit() {
		const text = signalText.trim();
		if (text && connected) {
			dispatch('signal', { text });
			signalText = '';
			inputElement.blur();
		}
	}
	
	function handleKeydown(event) {
		if (event.key === 'Enter') {
			event.preventDefault();
			handleSubmit();
		}
	}
</script>

<div class="signal-input-container">
	<div class="input-wrapper">
		<input
			bind:this={inputElement}
			bind:value={signalText}
			on:keydown={handleKeydown}
			placeholder={connected ? "Share a spark..." : "Connecting..."}
			disabled={!connected}
			maxlength="100"
			class="signal-input"
		/>
		<button 
			on:click={handleSubmit}
			disabled={!connected || !signalText.trim()}
			class="bloom-button"
			title="Send signal"
		>
			🌸
		</button>
	</div>
	<div class="input-hint">
		{#if signalText.length > 80}
			<span class="char-count">{100 - signalText.length} characters left</span>
		{/if}
	</div>
</div>

<style>
	.signal-input-container {
		position: fixed;
		bottom: 2rem;
		left: 50%;
		transform: translateX(-50%);
		z-index: 100;
		width: 90%;
		max-width: 500px;
	}
	
	.input-wrapper {
		display: flex;
		gap: 0.5rem;
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 30px;
		padding: 0.5rem;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
	}
	
	.signal-input {
		flex: 1;
		background: transparent;
		border: none;
		color: white;
		font-size: 1rem;
		padding: 0.75rem 1.25rem;
		border-radius: 25px;
		outline: none;
		transition: all 0.3s ease;
	}
	
	.signal-input::placeholder {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.signal-input:focus {
		background: rgba(255, 255, 255, 0.1);
	}
	
	.signal-input:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.bloom-button {
		background: linear-gradient(135deg, #ff9a9e, #fecfef);
		border: none;
		border-radius: 50%;
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		cursor: pointer;
		transition: all 0.3s ease;
		box-shadow: 0 4px 15px rgba(255, 154, 158, 0.3);
	}
	
	.bloom-button:hover:not(:disabled) {
		transform: scale(1.05);
		box-shadow: 0 6px 20px rgba(255, 154, 158, 0.4);
	}
	
	.bloom-button:active:not(:disabled) {
		transform: scale(0.95);
	}
	
	.bloom-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
		box-shadow: 0 2px 10px rgba(255, 154, 158, 0.2);
	}
	
	.input-hint {
		text-align: center;
		margin-top: 0.5rem;
		font-size: 0.8rem;
		opacity: 0.7;
		min-height: 1rem;
	}
	
	.char-count {
		color: rgba(255, 255, 255, 0.8);
	}
	
	@media (max-width: 600px) {
		.signal-input-container {
			bottom: 1rem;
			width: 95%;
		}
		
		.signal-input {
			font-size: 16px; /* Prevents zoom on iOS */
		}
	}
</style>