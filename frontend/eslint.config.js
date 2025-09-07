import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
	js.configs.recommended,
	...svelte.configs['flat/recommended'],
	{
		languageOptions: {
			globals: {
				browser: true,
				es2017: true,
				node: true,
			},
		},
		rules: {
			'no-unused-vars': 'warn',
			'no-console': 'warn',
			'svelte/no-at-html-tags': 'error',
			'svelte/no-target-blank': 'error',
			'svelte/no-useless-mustaches': 'warn',
			'svelte/prefer-class-directive': 'warn',
			'svelte/require-optimized-style-attribute': 'warn',
			'svelte/shorthand-attribute': 'warn',
		},
		ignores: [
			'build/**',
			'.svelte-kit/**',
			'dist/**',
			'node_modules/**',
		],
	},
];