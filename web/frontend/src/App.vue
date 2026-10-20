<template>
  <n-config-provider :theme="darkTheme" :locale="naiveLocale" :date-locale="naiveDateLocale">
    <n-message-provider>
      <n-dialog-provider>
        <n-layout class="app-layout">
        <!-- 顶部 Header -->
        <n-layout-header bordered class="app-header">
          <div class="header-left">
            <n-button
              quaternary
              class="menu-toggle hide-tablet"
              @click="sidebarCollapsed = !sidebarCollapsed"
            >
              <template #icon>
                <n-icon><MenuOutline /></n-icon>
              </template>
            </n-button>
            <img src="/logo.svg" alt="logo" class="app-logo" />
            <span class="title">Codex Session Patcher</span>
          </div>
          <div class="header-right">
            <n-tooltip v-if="appVersion" trigger="hover" placement="bottom">
              <template #trigger>
                <a href="https://github.com/ryfineZ/codex-session-patcher" target="_blank" class="version-link" aria-label="Version">
                  v{{ appVersion }}
                </a>
              </template>
              {{ $t('common.version') }}
            </n-tooltip>

            <!-- GitHub -->
            <n-tooltip trigger="hover" placement="bottom">
              <template #trigger>
                <a href="https://github.com/ryfineZ/codex-session-patcher" target="_blank" class="social-link" aria-label="GitHub">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>
                </a>
              </template>
              GitHub
            </n-tooltip>

            <!-- X (Twitter) -->
            <n-tooltip trigger="hover" placement="bottom">
              <template #trigger>
                <a href="https://x.com/ZhangYufan73644" target="_blank" class="social-link" aria-label="X">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
              </template>
              X (Twitter)
            </n-tooltip>

            <!-- 微信公众号 -->
            <n-popover trigger="click" placement="bottom-end" :width="200">
              <template #trigger>
                <button class="social-link" aria-label="微信公众号">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.161 1.71-1.484 1.255-2.263 3.057-1.944 4.85.976 5.58 9.277 7.679 14.6 4.066.061-.04.135-.06.211-.06a.29.29 0 0 1 .089.014l1.523.868a.29.29 0 0 0 .14.047c.134 0 .24-.11.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1 .181-.555C23.002 17.394 24 15.829 24 14.098c0-3.226-3.13-5.765-7.062-5.24zm-3.85 3.045c.56 0 1.012.46 1.012 1.028a1.02 1.02 0 0 1-1.012 1.028 1.02 1.02 0 0 1-1.013-1.028c0-.568.453-1.028 1.013-1.028zm5.886 0c.56 0 1.012.46 1.012 1.028a1.02 1.02 0 0 1-1.012 1.028 1.02 1.02 0 0 1-1.013-1.028c0-.568.453-1.028 1.013-1.028z"/></svg>
                </button>
              </template>
              <div style="text-align: center; padding: 8px 0">
                <img src="/qr-wechat-mp.png" alt="微信公众号" style="width: 160px; height: 160px; border-radius: 4px" />
                <div style="margin-top: 8px; font-size: 12px; opacity: 0.7">钢之AI术师</div>
              </div>
            </n-popover>

            <!-- Buy me a coffee -->
            <n-button size="small" type="primary" class="sponsor-btn" @click="showSponsor = true">
              ☕ Buy me a coffee
            </n-button>

            <LocaleSwitch />
          </div>

          <!-- 赞助弹窗 -->
          <n-modal v-model:show="showSponsor" preset="card" :style="{ width: '320px' }" title="Buy me a coffee ☕">
            <n-tabs type="segment" size="small" v-model:value="sponsorTab">
              <n-tab-pane name="wechat" tab="微信赞赏">
                <div style="text-align: center; padding: 12px 0">
                  <img src="/qr-sponsor-wechat.png" alt="微信收款码" class="sponsor-qr sponsor-qr-square" />
                  <div class="sponsor-note">感谢支持！</div>
                </div>
              </n-tab-pane>
              <n-tab-pane name="crypto" tab="USDC (Arbitrum)">
                <div style="text-align: center; padding: 12px 0">
                  <img src="/qr-sponsor-crypto.png" alt="USDC 收款码" class="sponsor-qr sponsor-qr-wide" />
                  <div style="margin-top: 12px">
                    <n-text style="font-size: 11px; font-family: monospace; word-break: break-all; opacity: 0.8">
                      0xAeEBb76262D5D452Aa0D4b19E193Dd2402397d02
                    </n-text>
                  </div>
                  <n-button size="small" style="margin-top: 8px" @click="copyWalletAddr">复制地址</n-button>
                </div>
              </n-tab-pane>
              <n-tab-pane name="records" :tab="$t('sponsor.records')">
                <n-empty :description="$t('sponsor.noRecords')" style="padding: 20px 0" />
              </n-tab-pane>
            </n-tabs>
          </n-modal>
        </n-layout-header>

        <!-- Tab 导航 -->
        <n-tabs v-model:value="activeTab" type="line" class="main-tabs" @update:value="handleTabChange">
          <n-tab name="enhance">
            <template #icon>
              <n-icon><SparklesOutline /></n-icon>
            </template>
            {{ $t('nav.enhance') }}
          </n-tab>
          <n-tab name="sessions">
            <template #icon>
              <n-icon><ListOutline /></n-icon>
            </template>
            {{ $t('nav.sessions') }}
          </n-tab>
          <n-tab name="settings">
            <template #icon>
              <n-icon><SettingsOutline /></n-icon>
            </template>
            {{ $t('nav.settings') }}
          </n-tab>
          <n-tab name="help">
            <template #icon>
              <n-icon><HelpCircleOutline /></n-icon>
            </template>
            {{ $t('nav.help') }}
          </n-tab>
          <n-tab name="cooperation">
            <template #icon>
              <n-icon><ChatbubblesOutline /></n-icon>
            </template>
            {{ $t('nav.cooperation') }}
          </n-tab>
        </n-tabs>

        <!-- 主内容区 -->
        <n-layout
          v-if="sessionsOpened"
          v-show="activeTab === 'sessions'"
          has-sider
          class="app-content"
        >
          <!-- 左侧会话列表 -->
          <n-layout-sider
            bordered
            :width="340"
            :collapsed-width="0"
            :collapsed="sidebarCollapsed"
            :native-scrollbar="false"
            class="session-sider"
            collapse-mode="transform"
            @collapse="sidebarCollapsed = true"
            @expand="sidebarCollapsed = false"
          >
            <SessionList />
          </n-layout-sider>

          <!-- 移动端遮罩 -->
          <div
            v-if="!sidebarCollapsed && isMobile"
            class="sidebar-overlay"
            @click="sidebarCollapsed = true"
          />

          <!-- 右侧内容区 -->
          <n-layout-content class="main-content">
            <PreviewPanel ref="previewPanelRef" v-model:cleanReasoning="cleanReasoning" />
            <ActionBar :preview-panel-ref="previewPanelRef" :clean-reasoning="cleanReasoning" />
          </n-layout-content>
        </n-layout>

        <!-- 其他 Tab 内容 -->
        <n-layout-content v-show="activeTab !== 'sessions'" class="tab-content">
          <div
            v-if="activeTab === 'enhance'"
            class="ad-layout"
            :style="getAdLayoutStyle('enhance')"
          >
            <AdSlot :slot="getAdSlot('enhance', 'left')" side="left" />
            <main class="ad-layout-main">
              <PromptEnhancePanel />
            </main>
            <AdSlot :slot="getAdSlot('enhance', 'right')" side="right" />
          </div>
          <div
            v-if="activeTab === 'settings'"
            class="ad-layout"
            :style="getAdLayoutStyle('settings')"
          >
            <AdSlot :slot="getAdSlot('settings', 'left')" side="left" />
            <main class="ad-layout-main">
              <SettingsPanel />
            </main>
            <AdSlot :slot="getAdSlot('settings', 'right')" side="right" />
          </div>
          <div
            v-if="activeTab === 'help'"
            class="ad-layout"
            :style="getAdLayoutStyle('help')"
          >
            <AdSlot :slot="getAdSlot('help', 'left')" side="left" />
            <main class="ad-layout-main">
              <HelpPanel />
            </main>
            <AdSlot :slot="getAdSlot('help', 'right')" side="right" />
          </div>
          <div
            v-if="activeTab === 'cooperation'"
            class="ad-layout"
            :style="getAdLayoutStyle('cooperation')"
          >
            <AdSlot :slot="getAdSlot('cooperation', 'left')" side="left" />
            <main class="ad-layout-main">
              <CooperationPanel />
            </main>
            <AdSlot :slot="getAdSlot('cooperation', 'right')" side="right" />
          </div>
        </n-layout-content>

        <!-- 底部日志面板 -->
        <LogPanel />
      </n-layout>
    </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, defineAsyncComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import { darkTheme, zhCN, dateZhCN, enUS, dateEnUS } from 'naive-ui'
import { SettingsOutline, MenuOutline, ListOutline, SparklesOutline, HelpCircleOutline, ChatbubblesOutline } from '@vicons/ionicons5'
import LogPanel from './components/LogPanel.vue'
import LocaleSwitch from './components/LocaleSwitch.vue'
import AdSlot from './components/AdSlot.vue'
import { useSessionStore } from './stores/sessionStore'
import { useSettingsStore } from './stores/settingsStore'
import { useLogStore } from './stores/logStore'
import { useLocaleStore } from './stores/localeStore'
import { api } from './services/api'

const SessionList = defineAsyncComponent(() => import('./components/SessionList.vue'))
const PreviewPanel = defineAsyncComponent(() => import('./components/PreviewPanel.vue'))
const ActionBar = defineAsyncComponent(() => import('./components/ActionBar.vue'))
const PromptEnhancePanel = defineAsyncComponent(() => import('./components/PromptEnhancePanel.vue'))
const SettingsPanel = defineAsyncComponent(() => import('./components/SettingsPanel.vue'))
const HelpPanel = defineAsyncComponent(() => import('./components/HelpPanel.vue'))
const CooperationPanel = defineAsyncComponent(() => import('./components/CooperationPanel.vue'))

const AD_TABS = ['enhance', 'settings', 'help', 'cooperation']
const AD_POSITIONS = ['left', 'right']
const AD_FITS = ['natural', 'contain', 'cover', 'fill']
const DEFAULT_AD_WIDTH = 'clamp(240px, 22vw, 420px)'
const DEFAULT_AD_MAX_HEIGHT = '72vh'
const DEFAULT_AD_BACKGROUND = 'var(--color-bg-1)'
const DEFAULT_AD_CONFIG_URL = 'https://leads.3jiezhiwai.com/api/sources/codex-session-patcher/ad-slots'
const AD_CONFIG_URL = import.meta.env.VITE_AD_CONFIG_URL || DEFAULT_AD_CONFIG_URL

const { t } = useI18n()
const activeTab = ref('enhance')
const sessionsOpened = ref(false)
const sidebarCollapsed = ref(false)
const isMobile = ref(false)
const showSponsor = ref(false)
const sponsorTab = ref('wechat')
const previewPanelRef = ref(null)
const cleanReasoning = ref(true)  // 是否清理推理内容
const appVersion = ref('')
const adSlots = ref([])

async function copyWalletAddr() {
  try {
    await navigator.clipboard.writeText('0xAeEBb76262D5D452Aa0D4b19E193Dd2402397d02')
  } catch {}
}
const sessionStore = useSessionStore()
const settingsStore = useSettingsStore()
const logStore = useLogStore()
const localeStore = useLocaleStore()

// Naive UI locale
const naiveLocale = computed(() => {
  return localeStore.currentLocale === 'en-US' ? enUS : zhCN
})

const naiveDateLocale = computed(() => {
  return localeStore.currentLocale === 'en-US' ? dateEnUS : dateZhCN
})

const adSlotMap = computed(() => {
  return new Map(adSlots.value.map(slot => [`${slot.tab}:${slot.position}`, slot]))
})

function getAdSlot(tab, position) {
  return adSlotMap.value.get(`${tab}:${position}`) || null
}

function getAdLayoutStyle(tab) {
  return {
    '--ad-left-width': getAdSlot(tab, 'left')?.width || DEFAULT_AD_WIDTH,
    '--ad-right-width': getAdSlot(tab, 'right')?.width || DEFAULT_AD_WIDTH
  }
}

function normalizeCssLength(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `${Math.max(80, Math.min(value, 600))}px`
  }

  if (typeof value !== 'string') {
    return ''
  }

  const trimmed = value.trim()
  const lengthPattern = /^-?\d+(\.\d+)?(px|rem|em|vw|vh|%)$/
  const clampPattern = /^clamp\(\s*-?\d+(\.\d+)?(px|rem|em|vw|vh|%)\s*,\s*-?\d+(\.\d+)?(px|rem|em|vw|vh|%)\s*,\s*-?\d+(\.\d+)?(px|rem|em|vw|vh|%)\s*\)$/

  return lengthPattern.test(trimmed) || clampPattern.test(trimmed) ? trimmed : ''
}

function normalizeAdWidth(slot) {
  const directWidth = normalizeCssLength(slot.width)
  if (directWidth) {
    return directWidth
  }

  const hasResponsiveWidth = slot.width_min || slot.width_vw || slot.width_max
  if (!hasResponsiveWidth) {
    return DEFAULT_AD_WIDTH
  }

  const min = normalizeCssLength(slot.width_min) || '190px'
  const middle = normalizeCssLength(slot.width_vw) || '17vw'
  const max = normalizeCssLength(slot.width_max) || '320px'
  return `clamp(${min}, ${middle}, ${max})`
}

function normalizeBackground(value) {
  if (typeof value !== 'string') {
    return DEFAULT_AD_BACKGROUND
  }

  const trimmed = value.trim()
  const colorPattern = /^(#[0-9a-fA-F]{3,8}|rgba?\([\d\s,.%]+\)|hsla?\([\d\s,.%deg]+\)|var\(--[a-zA-Z0-9-]+\)|transparent)$/
  return colorPattern.test(trimmed) ? trimmed : DEFAULT_AD_BACKGROUND
}

function normalizeImageUrl(value) {
  if (typeof value !== 'string') {
    return ''
  }

  const trimmed = value.trim()
  if (/^(https?:)?\/\//i.test(trimmed) || trimmed.startsWith('/')) {
    return trimmed
  }

  return ''
}

function normalizeClickUrl(value) {
  if (typeof value !== 'string') {
    return ''
  }

  const trimmed = value.trim()
  if (/^(https?:\/\/|mqqapi:\/\/|\/)/i.test(trimmed)) {
    return trimmed
  }

  return ''
}

function normalizeAdSlot(slot) {
  if (!slot || slot.enabled === false || !AD_TABS.includes(slot.tab) || !AD_POSITIONS.includes(slot.position)) {
    return null
  }

  const imageUrl = normalizeImageUrl(slot.image_url)
  if (!imageUrl) {
    return null
  }

  const fit = AD_FITS.includes(slot.fit) ? slot.fit : 'natural'
  return {
    tab: slot.tab,
    position: slot.position,
    imageUrl,
    clickUrl: normalizeClickUrl(slot.click_url),
    alt: typeof slot.alt === 'string' ? slot.alt.trim() : '',
    title: typeof slot.title === 'string' ? slot.title.trim() : '',
    width: normalizeAdWidth(slot),
    maxHeight: normalizeCssLength(slot.max_height) || DEFAULT_AD_MAX_HEIGHT,
    fit,
    background: normalizeBackground(slot.background)
  }
}

async function loadAdSlots() {
  try {
    const response = await fetch(AD_CONFIG_URL, { cache: 'no-cache' })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const config = await response.json()
    const slots = Array.isArray(config?.slots) ? config.slots : []
    adSlots.value = slots.map(normalizeAdSlot).filter(Boolean)
  } catch (error) {
    console.warn('Failed to load ad slots:', error)
    adSlots.value = []
  }
}

// 初始化：加载会话列表
sessionStore.fetchSessions()

// Tab 切换时加载设置
function handleTabChange(tab) {
  if (tab === 'sessions') {
    sessionsOpened.value = true
  }
  if (tab === 'settings') {
    settingsStore.loadSettings()
  }
}

// 响应式检测
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) {
    sidebarCollapsed.value = true
  }
}

async function loadAppVersion() {
  try {
    const result = await api.get('/version')
    appVersion.value = result.version || ''
  } catch {
    appVersion.value = ''
  }
}

onMounted(() => {
  checkMobile()
  loadAppVersion()
  loadAdSlots()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// WebSocket 连接管理
let ws = null
let reconnectTimer = null
const wsConnected = ref(false)

const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}/api/ws`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    wsConnected.value = true
    console.log('WebSocket connected')
  }

  ws.onclose = () => {
    wsConnected.value = false
    console.log('WebSocket disconnected, reconnecting...')
    // 3秒后重连
    reconnectTimer = setTimeout(connectWebSocket, 3000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'log') {
        const { level, message } = data.data
        logStore.addLog(message, level)
      }
    } catch (e) {
      console.error('WebSocket message parse error:', e)
    }
  }
}

connectWebSocket()

// 组件卸载时清理 WebSocket
onUnmounted(() => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  height: var(--header-height);
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-bg-1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-logo {
  width: 28px;
  height: 28px;
  display: block;
  flex-shrink: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  color: var(--color-text-3);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  text-decoration: none;
  transition: color 0.2s, background 0.2s;
}
.social-link:hover {
  color: var(--color-text-1);
  background: var(--color-bg-3);
}

.version-link {
  color: var(--color-primary-hover);
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  text-decoration: none;
  padding: 5px 8px;
  border: 1px solid var(--color-primary-pressed);
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}

.version-link:hover {
  color: var(--color-text-1);
  border-color: var(--color-primary-hover);
  background: var(--color-primary-pressed);
}

.sponsor-btn {
  font-size: 12px;
}

.sponsor-qr {
  display: block;
  margin: 0 auto;
  border-radius: var(--radius-md);
}

.sponsor-qr-square {
  width: 200px;
  height: auto;
}

.sponsor-qr-wide {
  width: 240px;
  max-width: 100%;
  height: auto;
}

.sponsor-note {
  margin-top: 12px;
  color: var(--color-text-3);
  font-size: 13px;
}

@media (max-width: 600px) {
  .sponsor-btn {
    display: none;
  }
}

.menu-toggle {
  display: none;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
}

.main-tabs {
  padding: 0 16px;
  background: var(--color-bg-1);
  border-bottom: 1px solid var(--color-border);
}

.main-tabs :deep(.n-tabs-nav) {
  padding: 0;
}

.app-content {
  flex: 1;
  min-height: 0;
}

.session-sider {
  background: var(--color-bg-1);
}

.sidebar-overlay {
  display: none;
}

.main-content {
  display: flex;
  flex-direction: column;
  padding: 16px;
  padding-bottom: 56px; /* 日志面板收起时的高度 + 安全边距 */
  background: var(--color-bg-2);
}

.tab-content {
  flex: 1;
  padding: 16px;
  padding-bottom: 56px;
  background: var(--color-bg-2);
  overflow: auto;
}

.ad-layout {
  width: 100%;
  max-width: none;
  margin: 0;
  display: grid;
  grid-template-columns: var(--ad-left-width) minmax(0, 800px) var(--ad-right-width);
  gap: 16px;
  align-items: start;
  justify-content: start;
}

.ad-layout-main {
  min-width: 0;
}

.ad-layout-main :deep(.prompt-enhance-panel),
.ad-layout-main :deep(.settings-panel),
.ad-layout-main :deep(.help-panel),
.ad-layout-main :deep(.cooperation-panel) {
  margin-left: 0;
  margin-right: 0;
}

/* 响应式布局 */
@media (max-width: 1480px) {
  .ad-layout {
    display: block;
    max-width: 960px;
  }

  .ad-layout :deep(.ad-slot-frame) {
    display: none;
  }
}

@media (max-width: 1024px) {
  .menu-toggle {
    display: flex;
  }

  .session-sider {
    position: fixed;
    top: calc(var(--header-height) + 40px);
    left: 0;
    bottom: 0;
    z-index: 100;
    background: var(--color-bg-1);
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    top: calc(var(--header-height) + 40px);
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--color-overlay);
    z-index: 99;
  }
}

@media (max-width: 768px) {
  .main-content, .tab-content {
    padding: 12px;
  }
}
</style>
