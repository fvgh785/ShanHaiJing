import { defineStore } from 'pinia'
import { fetchRecords, createRecord, updateRecord, fetchRecord } from '../api/records'

export const useRecordsStore = defineStore('records', {
  state: () => ({
    currentRecord: {
      plan_id: null,
      creature_name: '',
      work_date: new Date().toISOString().slice(0, 10),
      tools_used: [],
      style_tag: null,
      baseline_id: null,
      image_prompt: '',
      video_prompt: '',
      negative_prompt: '',
      style_review: null,
      points_consumed: 0,
      output_url: '',
      intermediate_urls: [],
      notes: '',
      status: 'in_progress',
      is_temporary: false
    },
    records: [],
    total: 0,
    loading: false,
    error: null
  }),

  actions: {
    resetCurrentRecord() {
      this.currentRecord = {
        plan_id: null,
        creature_name: '',
        work_date: new Date().toISOString().slice(0, 10),
        tools_used: [],
        style_tag: null,
        baseline_id: null,
        image_prompt: '',
        video_prompt: '',
        negative_prompt: '',
        style_review: null,
        points_consumed: 0,
        output_url: '',
        intermediate_urls: [],
        notes: '',
        status: 'in_progress',
        is_temporary: false
      }
    },

    async loadRecord(id) {
      try {
        const res = await fetchRecord(id)
        const data = res.data || res
        this.currentRecord = {
          ...this.currentRecord,
          ...data,
          work_date: data.work_date ? data.work_date.slice(0, 10) : this.currentRecord.work_date
        }
      } catch (err) {
        throw err
      }
    },

    async saveRecord(recordData) {
      const payload = { ...recordData }
      delete payload.is_temporary
      delete payload.style_review

      const res = await createRecord(payload)
      return res.data || res
    },

    async updateExistingRecord(id, recordData) {
      const payload = { ...recordData }
      delete payload.is_temporary
      delete payload.style_review

      const res = await updateRecord(id, payload)
      return res.data || res
    },

    async fetchRecordList(params = {}) {
      this.loading = true
      this.error = null
      try {
        const res = await fetchRecords(params)
        this.records = res.data || []
        this.total = res.pagination?.total || this.records.length
      } catch (err) {
        this.error = err.message || '获取记录失败'
      } finally {
        this.loading = false
      }
    }
  }
})
