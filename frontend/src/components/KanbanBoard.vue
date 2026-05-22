<template>
  <div class="kanban-board">
    <div v-for="col in columns" :key="col.status" class="kanban-column">
      <div class="column-header">
        <n-tag :type="col.type || 'default'" size="medium" :bordered="false">
          {{ col.label }}
        </n-tag>
        <n-text depth="3" class="column-count">{{ getColumnItems(col.status).length }}</n-text>
      </div>
      <draggable
        :list="getColumnItems(col.status)"
        :group="{ name: 'plans', pull: true, put: true }"
        :item-key="'id'"
        class="column-body"
        ghost-class="ghost-card"
        :animation="200"
        @change="(evt) => onDragChange(evt, col.status)"
      >
        <template #item="{ element }">
          <div class="plan-card" @click="$emit('card-click', element)">
            <div class="card-header">
              <n-text strong>{{ element.creature_name }}</n-text>
              <div class="card-priority">
                <span v-for="n in (element.priority || 0)" :key="n" class="star">&#9733;</span>
              </div>
            </div>
            <div class="card-meta">
              <n-tag size="tiny" :bordered="false" type="info">{{ element.juan }}</n-tag>
              <n-tag v-if="element.recommended_tool" size="tiny" :bordered="false" type="success">
                {{ element.recommended_tool }}
              </n-tag>
            </div>
            <div class="card-footer">
              <n-text depth="3" class="card-date">{{ element.planned_date || '-' }}</n-text>
            </div>
          </div>
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup>
import draggable from 'vuedraggable'

const props = defineProps({
  plans: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] }
})

const emit = defineEmits(['status-change', 'card-click'])

function getColumnItems(status) {
  return props.plans.filter((p) => p.status === status)
}

function onDragChange(evt, newStatus) {
  if (evt.added) {
    const plan = evt.added.element
    emit('status-change', plan.id, newStatus)
  }
}
</script>

<style scoped>
.kanban-board {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  min-height: 400px;
  padding-bottom: 16px;
}

.kanban-column {
  flex: 1;
  min-width: 260px;
  max-width: 360px;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 12px;
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.column-count {
  font-size: 13px;
}

.column-body {
  min-height: 200px;
}

.plan-card {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  border: 1px solid #eee;
  transition: box-shadow 0.2s;
}

.plan-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.card-priority {
  display: flex;
}

.star {
  color: #f0a020;
  font-size: 14px;
}

.card-meta {
  display: flex;
  gap: 4px;
  margin-bottom: 6px;
}

.card-footer {
  font-size: 12px;
}

.card-date {
  font-size: 12px;
}

.ghost-card {
  opacity: 0.4;
  background: #e0d4f5;
}
</style>
