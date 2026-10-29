export const AI_PROVIDER_PRESETS = [
  {
    key: 'minimax',
    label: 'MiniMax',
    defaultRegion: 'global_en',
    defaultModel: 'MiniMax-M3.1-Flash',
    models: [
      {
        label: 'MiniMax-M3.1-Flash',
        value: 'MiniMax-M3.1-Flash',
        contextWindow: 1000000,
        maxOutputTokens: 524288,
        inputModalities: ['text', 'image', 'video'],
        thinking: ['adaptive'],
        reasoningEfforts: ['low', 'medium', 'high', 'xhigh', 'max'],
        // Global pay-as-you-go pricing; regional billing may differ.
        pricingUsdPerMillionTokens: {
          input: 0.15,
          output: 0.6,
          cacheRead: 0.015,
          cacheWrite: null
        }
      },
      {
        label: 'MiniMax-M3',
        value: 'MiniMax-M3',
        contextWindow: 1000000,
        inputModalities: ['text', 'image', 'video'],
        thinking: ['adaptive', 'disabled'],
        // Global standard tier, up to 512k input tokens.
        pricingUsdPerMillionTokens: {
          input: 0.3,
          output: 1.2,
          cacheRead: 0.06,
          cacheWrite: null
        },
        pricingAbove512kUsdPerMillionTokens: {
          input: 0.6,
          output: 2.4,
          cacheRead: 0.12,
          cacheWrite: null
        }
      }
    ],
    regions: [
      {
        label: 'Global',
        value: 'global_en',
        openaiBaseUrl: 'https://api.minimax.io/v1',
        anthropicBaseUrl: 'https://api.minimax.io/anthropic',
        docsRoot: 'https://platform.minimax.io/docs'
      },
      {
        label: 'China',
        value: 'cn_zh',
        openaiBaseUrl: 'https://api.minimaxi.com/v1',
        anthropicBaseUrl: 'https://api.minimaxi.com/anthropic',
        docsRoot: 'https://platform.minimaxi.com/docs'
      }
    ]
  }
]

export function getProviderPreset(key) {
  return AI_PROVIDER_PRESETS.find((provider) => provider.key === key) || null
}
