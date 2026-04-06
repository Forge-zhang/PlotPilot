<template>
  <div class="fs-suggestions">
    <n-alert type="info" :show-icon="true" style="margin-bottom: 12px; font-size: 12px">
      <strong>写</strong>：即时计算，默认不落库（后续可接向量库 Embedding）。<strong>读</strong>：生成前勾选项可并入节拍提示（与「伏笔账本」同一数据源）。
    </n-alert>

    <n-empty v-if="!currentChapterNumber" description="请先在左侧选择章节">
      <template #icon>
        <span style="font-size: 40px">📌</span>
      </template>
    </n-empty>

    <n-space v-else vertical :size="12" style="width: 100%">
      <n-form-item label="本章大纲 / 要点" label-placement="top" :show-feedback="false">
        <n-input
          v-model:value="outlineDraft"
          type="textarea"
          placeholder="粘贴或编写本章大纲，用于与待回收伏笔做相似度（当前为词重叠启发式）"
          :autosize="{ minRows: 4, maxRows: 12 }"
        />
      </n-form-item>
      <n-button type="primary" size="small" :loading="loading" @click="runSuggest">
        分析建议回收项
      </n-button>

      <n-text v-if="note" depth="3" style="font-size: 11px">{{ note }}</n-text>

      <n-empty v-if="ran && items.length === 0" description="暂无达到阈值的匹配，可调低大纲信息量或稍后在账本中手动核销" />

      <n-space v-if="items.length" vertical :size="8">
        <n-text strong style="font-size: 13px">💡 建议顺手回收（勾选便于你自行记入节拍提示）</n-text>
        <n-card
          v-for="row in items"
          :key="row.entry.id"
          size="small"
          :bordered="true"
        >
          <n-space align="flex-start" :size="10">
            <n-checkbox
              :checked="picked.has(row.entry.id)"
              @update:checked="(v: boolean) => togglePick(row.entry.id, v)"
            />
            <div style="flex: 1; min-width: 0">
              <n-space align="center" :size="8" wrap>
                <n-tag size="tiny" round type="warning">分 {{ row.score.toFixed(2) }}</n-tag>
                <n-tag size="tiny" round>埋设 第{{ row.entry.chapter }}章</n-tag>
              </n-space>
              <p class="clue-text">{{ row.entry.hidden_clue }}</p>
              <n-text depth="3" style="font-size: 11px">{{ row.reason }}</n-text>
            </div>
          </n-space>
        </n-card>
      </n-space>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { foreshadowApi } from '../../api/foreshadow'
import type { ChapterForeshadowSuggestionItem } from '../../api/foreshadow'

const props = defineProps<{
  slug: string
  currentChapterNumber?: number | null
}>()

const message = useMessage()
const outlineDraft = ref('')
const loading = ref(false)
const ran = ref(false)
const items = ref<ChapterForeshadowSuggestionItem[]>([])
const note = ref('')
const picked = ref<Set<string>>(new Set())

function togglePick(id: string, on: boolean) {
  const next = new Set(picked.value)
  if (on) {
    next.add(id)
  } else {
    next.delete(id)
  }
  picked.value = next
}

async function runSuggest() {
  const ch = props.currentChapterNumber
  if (!ch) return
  loading.value = true
  ran.value = true
  try {
    const res = await foreshadowApi.chapterSuggestions(props.slug, ch, outlineDraft.value, {
      min_score: 0.06,
      limit: 16,
    })
    items.value = res.items
    note.value = res.note
    picked.value = new Set()
  } catch {
    message.error('建议分析失败，请确认后端已更新')
    items.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => props.currentChapterNumber,
  () => {
    ran.value = false
    items.value = []
    note.value = ''
    picked.value = new Set()
  }
)
</script>

<style scoped>
.fs-suggestions {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 16px 20px;
}

.clue-text {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.5;
}
</style>
