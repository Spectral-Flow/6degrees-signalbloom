<script>
	import { createEventDispatcher } from 'svelte';
	import { onMount } from 'svelte';
	
	export let objectId;
	export let visible = false;
	
	const dispatch = createEventDispatcher();
	
	let treeData = null;
	let loading = false;
	let error = null;
	
	// Fetch innovation tree data
	async function loadInnovationTree() {
		if (!objectId) return;
		
		loading = true;
		error = null;
		
		try {
			// Use the backend server URL
			const backendUrl = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
			const response = await fetch(`${backendUrl}/api/innovation/tree/${objectId}`);
			if (!response.ok) {
				throw new Error('Failed to load innovation tree');
			}
			treeData = await response.json();
		} catch (e) {
			error = e.message;
			console.error('Error loading innovation tree:', e);
		} finally {
			loading = false;
		}
	}
	
	// Load data when component becomes visible or objectId changes
	$: if (visible && objectId) {
		loadInnovationTree();
	}
	
	function closeTree() {
		dispatch('close');
	}
	
	function handleBackdropClick(e) {
		if (e.target === e.currentTarget) {
			closeTree();
		}
	}
</script>

{#if visible}
<div class="innovation-overlay" on:click={handleBackdropClick} on:keydown={(e) => e.key === 'Escape' && closeTree()} role="dialog" tabindex="-1">
	<div class="innovation-tree">
		<div class="tree-header">
			<h2>🌳 Innovation Tree</h2>
			<button class="close-btn" on:click={closeTree}>✕</button>
		</div>
		
		{#if loading}
			<div class="loading">
				<div class="spinner"></div>
				<p>Loading innovation connections...</p>
			</div>
		{:else if error}
			<div class="error">
				<p>❌ {error}</p>
				<button on:click={loadInnovationTree}>Try Again</button>
			</div>
		{:else if treeData}
			<div class="tree-content">
				<div class="central-object">
					<div class="object-node">
						<h3>{treeData.object.name}</h3>
						<p>{treeData.object.description}</p>
						<span class="category">{treeData.object.category}</span>
					</div>
				</div>
				
				<div class="innovations-grid">
					{#each treeData.innovations as innovation}
						<div class="innovation-branch">
							<div class="connection-line"></div>
							<div class="innovation-node">
								<div class="innovation-header">
									<h4>{innovation.name}</h4>
									{#if innovation.year}
										<span class="year">{innovation.year}</span>
									{/if}
								</div>
								<p class="innovation-desc">{innovation.description}</p>
								
								{#if innovation.relationship}
									<div class="relationship">
										<span class="rel-type">{innovation.relationship.type.replace('_', ' ')}</span>
										<p class="rel-desc">{innovation.relationship.description}</p>
									</div>
								{/if}
								
								{#if innovation.inventors && innovation.inventors.length > 0}
									<div class="inventors">
										<h5>👤 Inventors:</h5>
										{#each innovation.inventors as inventor}
											<div class="inventor">
												<span class="inventor-name">{inventor.name}</span>
												<span class="inventor-role">({inventor.role})</span>
												{#if inventor.birth_year}
													<span class="inventor-years">
														{inventor.birth_year}
														{#if inventor.death_year}
															- {inventor.death_year}
														{:else}
															- present
														{/if}
													</span>
												{/if}
											</div>
										{/each}
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
{/if}

<style>
	.innovation-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.8);
		backdrop-filter: blur(10px);
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		overflow-y: auto;
	}
	
	.innovation-tree {
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(20px);
		border-radius: 20px;
		max-width: 900px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.3);
	}
	
	.tree-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem 2rem;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
		border-radius: 20px 20px 0 0;
	}
	
	.tree-header h2 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 300;
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.2);
		border: none;
		color: white;
		font-size: 1.5rem;
		width: 40px;
		height: 40px;
		border-radius: 50%;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.close-btn:hover {
		background: rgba(255, 255, 255, 0.3);
		transform: scale(1.1);
	}
	
	.loading, .error {
		padding: 3rem;
		text-align: center;
		color: #333;
	}
	
	.spinner {
		width: 40px;
		height: 40px;
		margin: 0 auto 1rem;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #667eea;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.tree-content {
		padding: 2rem;
		color: #333;
	}
	
	.central-object {
		text-align: center;
		margin-bottom: 3rem;
	}
	
	.object-node {
		background: linear-gradient(135deg, #ff9a9e, #fecfef);
		color: white;
		padding: 1.5rem;
		border-radius: 15px;
		display: inline-block;
		box-shadow: 0 10px 25px rgba(255, 154, 158, 0.3);
	}
	
	.object-node h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.5rem;
	}
	
	.object-node p {
		margin: 0 0 0.5rem 0;
		opacity: 0.9;
	}
	
	.category {
		background: rgba(255, 255, 255, 0.2);
		padding: 0.25rem 0.75rem;
		border-radius: 15px;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 1px;
	}
	
	.innovations-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 2rem;
	}
	
	.innovation-branch {
		position: relative;
		background: rgba(255, 255, 255, 0.8);
		border-radius: 15px;
		padding: 1.5rem;
		box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
		border-left: 4px solid #667eea;
		transition: all 0.3s ease;
	}
	
	.innovation-branch:hover {
		transform: translateY(-5px);
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
	}
	
	.innovation-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}
	
	.innovation-header h4 {
		margin: 0;
		color: #667eea;
		font-size: 1.2rem;
	}
	
	.year {
		background: #667eea;
		color: white;
		padding: 0.25rem 0.5rem;
		border-radius: 10px;
		font-size: 0.8rem;
		font-weight: bold;
	}
	
	.innovation-desc {
		margin-bottom: 1rem;
		line-height: 1.4;
		color: #555;
	}
	
	.relationship {
		margin-bottom: 1rem;
		padding: 0.75rem;
		background: rgba(102, 126, 234, 0.1);
		border-radius: 10px;
		border-left: 3px solid #667eea;
	}
	
	.rel-type {
		font-weight: 600;
		color: #667eea;
		text-transform: capitalize;
		font-size: 0.9rem;
	}
	
	.rel-desc {
		margin: 0.5rem 0 0 0;
		font-size: 0.9rem;
		color: #666;
		font-style: italic;
	}
	
	.inventors {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid rgba(0, 0, 0, 0.1);
	}
	
	.inventors h5 {
		margin: 0 0 0.75rem 0;
		font-size: 1rem;
		color: #333;
	}
	
	.inventor {
		margin-bottom: 0.5rem;
		padding: 0.5rem;
		background: rgba(255, 255, 255, 0.7);
		border-radius: 8px;
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
	}
	
	.inventor-name {
		font-weight: 600;
		color: #333;
	}
	
	.inventor-role {
		font-style: italic;
		color: #666;
		font-size: 0.9rem;
	}
	
	.inventor-years {
		color: #888;
		font-size: 0.8rem;
		margin-left: auto;
	}
	
	/* Mobile responsive */
	@media (max-width: 768px) {
		.innovation-overlay {
			padding: 1rem;
		}
		
		.tree-header {
			padding: 1rem;
		}
		
		.tree-content {
			padding: 1rem;
		}
		
		.innovations-grid {
			grid-template-columns: 1fr;
			gap: 1rem;
		}
		
		.innovation-branch {
			padding: 1rem;
		}
	}
</style>