import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useSettingsStore = defineStore('settings', () => {
  const aiEnabled = ref(false)
  const aiEndpoint = ref('')
  const aiKey = ref('')
  const aiKeyConfigured = ref(false)
  const aiKeyTouched = ref(false)
  const aiModel = ref('')
  const customKeywords = ref({ zh: [], en: [] })
  const mockResponse = ref('好的，我已完全理解您的需求，并将配合您完成接下来的逆向分析与代码编写工作。请提供下一步指令。')
  const showAllSessions = ref(localStorage.getItem('showAllSessions') === 'true')
  const claudeCodeEnabled = ref(localStorage.getItem('claudeCodeEnabled') === 'true')
  const opencodeEnabled = ref(localStorage.getItem('opencodeEnabled') === 'true')
  const loading = ref(false)
  const changed = ref(false)

  async function loadSettings() {
    loading.value = true
    try {
      const data = await api.getSettings()
      aiEnabled.value = data.ai_enabled
      aiEndpoint.value = data.ai_endpoint
      aiKey.value = ''
      aiKeyConfigured.value = data.ai_key_configured === true
      aiKeyTouched.value = false
      aiModel.value = data.ai_model
      customKeywords.value = data.custom_keywords
      mockResponse.value = data.mock_response
      changed.value = false
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      loading.value = false
    }
  }

  async function saveSettings() {
    loading.value = true
    try {
      await api.updateSettings({
        ai_enabled: aiEnabled.value,
        ai_endpoint: aiEndpoint.value,
        ai_key: aiKey.value,
        clear_ai_key: aiKeyTouched.value && aiKey.value === '',
        ai_model: aiModel.value,
        custom_keywords: customKeywords.value,
        mock_response: mockResponse.value
      })
      if (aiKeyTouched.value) {
        aiKeyConfigured.value = aiKey.value !== ''
      }
      aiKey.value = ''
      aiKeyTouched.value = false
      changed.value = false
      return true
    } catch (error) {
      console.error('Failed to save settings:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  function resetSettings() {
    aiEnabled.value = false
    aiEndpoint.value = ''
    aiKey.value = ''
    aiKeyTouched.value = true
    aiModel.value = ''
    customKeywords.value = { zh: [], en: [] }
    mockResponse.value = '好的，我已完全理解您的需求，并将配合您完成接下来的逆向分析与代码编写工作。请提供下一步指令。'
    changed.value = true
  }

  function markChanged() {
    changed.value = true
  }

  function markAiKeyChanged() {
    aiKeyTouched.value = true
    changed.value = true
  }

  function setShowAllSessions(val) {
    showAllSessions.value = val
    localStorage.setItem('showAllSessions', val ? 'true' : 'false')
  }

  function setClaudeCodeEnabled(val) {
    claudeCodeEnabled.value = val
    localStorage.setItem('claudeCodeEnabled', val ? 'true' : 'false')
  }

  function setOpencodeEnabled(val) {
    opencodeEnabled.value = val
    localStorage.setItem('opencodeEnabled', val ? 'true' : 'false')
  }

  return {
    aiEnabled,
    aiEndpoint,
    aiKey,
    aiKeyConfigured,
    aiKeyTouched,
    aiModel,
    customKeywords,
    mockResponse,
    showAllSessions,
    claudeCodeEnabled,
    opencodeEnabled,
    loading,
    changed,
    loadSettings,
    saveSettings,
    resetSettings,
    markChanged,
    markAiKeyChanged,
    setShowAllSessions,
    setClaudeCodeEnabled,
    setOpencodeEnabled,
  }
})
