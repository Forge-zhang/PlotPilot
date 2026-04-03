<template>
  <div class="story-structure">
    <div class="structure-body" v-if="treeData.length > 0">
      <n-tree
        :data="treeData"
        :node-props="nodeProps"
        :render-label="renderLabel"
        :render-suffix="renderSuffix"
        :selected-keys="selectedKeys"
        block-line
        expand-on-click
        selectable
        @update:selected-keys="handleSelect"
      />
    </div>

    <n-empty
      v-else-if="!loading"
      description="暂无叙事结构，请先执行「AI 初始规划」"
      class="structure-empty"
    />

    <n-spin v-if="loading" class="structure-loading" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import { NTree, NEmpty, NSpin, NTag, useMessage } from 'naive-ui'
import { structureApi, type StoryNode } from '@/api/structure'

const props = defineProps<{
  slug: string
  currentChapterId?: number | null
}>()

const emit = defineEmits<{
  selectChapter: [id: number]
}>()

const message = useMessage()

const loading = ref(false)
const treeData = ref<StoryNode[]>([])
const selectedKeys = ref<string[]>([])

// 监听当前章节变化，更新选中状态
watch(() => props.currentChapterId, (chapterId) => {
  if (chapterId) {
    const chapterKey = `chapter-${props.slug}-chapter-${chapterId}`
    selectedKeys.value = [chapterKey]
  } else {
    selectedKeys.value = []
  }
}, { immediate: true })

// 转换节点为 NTree 格式
const convertToTreeNode = (node: StoryNode): any => {
  return {
    key: node.id,
    label: node.display_name,
    ...node,
    children: node.children?.map(convertToTreeNode) || []
  }
}

// 加载结构树
const loadTree = async () => {
  loading.value = true
  try {
    const res = await structureApi.getTree(props.slug)

    // 如果没有结构，自动初始化第一幕
    if (!res.tree || res.tree.length === 0) {
      await initializeStructure()
      return
    }

    treeData.value = res.tree.map(convertToTreeNode)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '加载结构失败')
  } finally {
    loading.value = false
  }
}

// 初始化叙事结构（AI 生成第一幕）
const initializeStructure = async () => {
  try {
    message.info('正在生成第一幕...')
    const res = await structureApi.initializeStructure(props.slug)

    if (res.success) {
      message.success(res.message || '第一幕已创建')
      // 重新加载树
      const treeRes = await structureApi.getTree(props.slug)
      treeData.value = treeRes.tree.map(convertToTreeNode)
    } else {
      message.warning(res.message || '结构已存在')
    }
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '初始化失败')
  } finally {
    loading.value = false
  }
}

// 选择节点
const handleSelect = (keys: string[]) => {
  if (keys.length > 0) {
    const findNode = (nodes: StoryNode[], id: string): StoryNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node
        if (node.children) {
          const found = findNode(node.children, id)
          if (found) return found
        }
      }
      return null
    }

    const node = findNode(treeData.value, keys[0])
    if (node && node.node_type === 'chapter') {
      // 从 chapter-novel-xxx-chapter-123 中提取章节 ID
      const match = node.id.match(/chapter-(\d+)$/)
      if (match) {
        const chapterId = parseInt(match[1])
        emit('selectChapter', chapterId)
      }
    }
  }
}

// 渲染节点标签
const renderLabel = ({ option }: { option: StoryNode }) => {
  const elements: any[] = [
    h('span', { class: 'node-icon' }, option.icon),
    h('span', { class: 'node-title' }, option.display_name)
  ]

  // 章节节点显示状态标签
  if (option.node_type === 'chapter') {
    const hasContent = option.word_count && option.word_count > 0
    elements.push(
      h(NTag, {
        size: 'small',
        type: hasContent ? 'success' : 'default',
        round: true,
        style: { marginLeft: '8px' }
      }, () => hasContent ? '已收稿' : '未收稿')
    )
  }

  return h('span', { class: 'node-label' }, elements)
}

// 渲染节点后缀（章节范围/字数）
const renderSuffix = ({ option }: { option: StoryNode }) => {
  if (option.node_type === 'chapter' && option.word_count) {
    return h('span', { class: 'node-range' }, `${option.word_count}字`)
  }
  if (option.chapter_start && option.chapter_end) {
    return h('span', { class: 'node-range' },
      `${option.chapter_start}-${option.chapter_end}章 (${option.chapter_count})`
    )
  }
  return null
}

// 节点属性
const nodeProps = ({ option }: { option: StoryNode }) => {
  return {
    class: `node-level-${option.level}`
  }
}

onMounted(() => {
  loadTree()
})
</script>

<style scoped>
.story-structure {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 0;
}

.structure-body {
  flex: 1;
  overflow: auto;
}

.structure-empty {
  padding: 40px 0;
}

.structure-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  font-size: 16px;
}

.node-title {
  font-size: 13px;
}

.node-range {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.node-level-1 {
  font-weight: 600;
}

.node-level-2 {
  font-weight: 500;
}

.node-level-3 {
  font-weight: normal;
}

.node-level-4 {
  font-weight: normal;
  font-size: 13px;
}
</style>
