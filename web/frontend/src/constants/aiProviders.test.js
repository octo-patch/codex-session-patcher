import assert from 'node:assert/strict'
import test from 'node:test'
import { AI_PROVIDER_PRESETS, getProviderPreset } from './aiProviders.js'

test('MiniMax offers Flash first and M3 while keeping custom lookup optional', () => {
  const provider = getProviderPreset('minimax')
  assert.ok(AI_PROVIDER_PRESETS.includes(provider))
  assert.equal(provider.defaultModel, 'MiniMax-M3.1-Flash')
  assert.deepEqual(provider.models.map(({ value }) => value), ['MiniMax-M3.1-Flash', 'MiniMax-M3'])
  assert.equal(getProviderPreset('custom'), null)
  assert.equal(getProviderPreset(null), null)
  assert.equal(provider.defaultRegion, 'global_en')
  assert.deepEqual(provider.regions.map(({ openaiBaseUrl }) => openaiBaseUrl), [
    'https://api.minimax.io/v1',
    'https://api.minimax.cn/v1'
  ])
})

test('current model capabilities and global pricing match the published contract', () => {
  const [flash, m3] = getProviderPreset('minimax').models
  for (const model of [flash, m3]) {
    assert.equal(model.contextWindow, 1000000)
    assert.deepEqual(model.inputModalities, ['text', 'image', 'video'])
    assert.equal(model.pricingUsdPerMillionTokens.cacheWrite, null)
  }
  assert.equal(flash.maxOutputTokens, 524288)
  assert.deepEqual(flash.thinking, ['adaptive'])
  assert.deepEqual(flash.reasoningEfforts, ['low', 'medium', 'high', 'xhigh', 'max'])
  assert.deepEqual(flash.pricingUsdPerMillionTokens, {
    input: 0.15, output: 0.6, cacheRead: 0.015, cacheWrite: null
  })
  assert.deepEqual(m3.thinking, ['adaptive', 'disabled'])
  assert.deepEqual(m3.pricingUsdPerMillionTokens, {
    input: 0.3, output: 1.2, cacheRead: 0.06, cacheWrite: null
  })
  assert.deepEqual(m3.pricingAbove512kUsdPerMillionTokens, {
    input: 0.6, output: 2.4, cacheRead: 0.12, cacheWrite: null
  })
})
