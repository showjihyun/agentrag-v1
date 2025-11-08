"use client"

import React, { useState, useEffect } from 'react'
import { Plus, Trash2, Edit2, Eye, EyeOff, Save, X } from 'lucide-react'

interface Variable {
  id: string
  name: string
  scope: 'global' | 'workspace' | 'user' | 'agent'
  scope_id?: string
  value_type: 'string' | 'number' | 'boolean' | 'json'
  value: string
  is_secret: boolean
  created_at: string
  updated_at: string
}

interface VariableManagerProps {
  workflowId?: string
  agentId?: string
  onVariableChange?: (variables: Variable[]) => void
}

export function VariableManager({ workflowId, agentId, onVariableChange }: VariableManagerProps) {
  const [variables, setVariables] = useState<Variable[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [revealedSecrets, setRevealedSecrets] = useState<Set<string>>(new Set())
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    scope: 'agent' as Variable['scope'],
    scope_id: agentId || '',
    value_type: 'string' as Variable['value_type'],
    value: '',
    is_secret: false,
  })

  useEffect(() => {
    loadVariables()
  }, [agentId])

  const loadVariables = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (agentId) {
        params.append('scope', 'agent')
        params.append('scope_id', agentId)
      }
      
      const response = await fetch(`/api/agent-builder/variables?${params}`)
      if (!response.ok) throw new Error('Failed to load variables')
      
      const data = await response.json()
      setVariables(data.variables)
      onVariableChange?.(data.variables)
    } catch (error) {
      console.error('Error loading variables:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      const response = await fetch('/api/agent-builder/variables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
      
      if (!response.ok) throw new Error('Failed to create variable')
      
      await loadVariables()
      setShowAddForm(false)
      resetForm()
    } catch (error) {
      console.error('Error creating variable:', error)
      alert('Failed to create variable')
    }
  }

  const handleUpdate = async (id: string) => {
    try {
      const variable = variables.find(v => v.id === id)
      if (!variable) return
      
      const response = await fetch(`/api/agent-builder/variables/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          value: formData.value,
          value_type: formData.value_type,
        }),
      })
      
      if (!response.ok) throw new Error('Failed to update variable')
      
      await loadVariables()
      setEditingId(null)
      resetForm()
    } catch (error) {
      console.error('Error updating variable:', error)
      alert('Failed to update variable')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this variable?')) return
    
    try {
      const response = await fetch(`/api/agent-builder/variables/${id}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) throw new Error('Failed to delete variable')
      
      await loadVariables()
    } catch (error) {
      console.error('Error deleting variable:', error)
      alert('Failed to delete variable')
    }
  }

  const toggleSecretVisibility = (id: string) => {
    setRevealedSecrets(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const startEdit = (variable: Variable) => {
    setEditingId(variable.id)
    setFormData({
      name: variable.name,
      scope: variable.scope,
      scope_id: variable.scope_id || '',
      value_type: variable.value_type,
      value: variable.is_secret ? '' : variable.value,
      is_secret: variable.is_secret,
    })
  }

  const cancelEdit = () => {
    setEditingId(null)
    resetForm()
  }

  const resetForm = () => {
    setFormData({
      name: '',
      scope: 'agent',
      scope_id: agentId || '',
      value_type: 'string',
      value: '',
      is_secret: false,
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Workflow Variables</h3>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Variable
        </button>
      </div>

      {/* Add/Edit Form */}
      {(showAddForm || editingId) && (
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h4 className="font-medium mb-4">
            {editingId ? 'Edit Variable' : 'New Variable'}
          </h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={!!editingId}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 disabled:opacity-50"
                placeholder="variable_name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                value={formData.value_type}
                onChange={(e) => setFormData({ ...formData, value_type: e.target.value as Variable['value_type'] })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
              >
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
                <option value="json">JSON</option>
              </select>
            </div>

            {!editingId && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-1">Scope</label>
                  <select
                    value={formData.scope}
                    onChange={(e) => setFormData({ ...formData, scope: e.target.value as Variable['scope'] })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
                  >
                    <option value="global">Global</option>
                    <option value="workspace">Workspace</option>
                    <option value="user">User</option>
                    <option value="agent">Agent</option>
                  </select>
                </div>

                <div className="flex items-center">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_secret}
                      onChange={(e) => setFormData({ ...formData, is_secret: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-medium">Secret</span>
                  </label>
                </div>
              </>
            )}

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Value</label>
              {formData.value_type === 'json' ? (
                <textarea
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 font-mono text-sm"
                  rows={4}
                  placeholder='{"key": "value"}'
                />
              ) : (
                <input
                  type={formData.is_secret ? 'password' : 'text'}
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
                  placeholder="Enter value"
                />
              )}
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => editingId ? handleUpdate(editingId) : handleCreate()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Save className="w-4 h-4" />
              {editingId ? 'Update' : 'Create'}
            </button>
            <button
              onClick={() => {
                if (editingId) {
                  cancelEdit()
                } else {
                  setShowAddForm(false)
                  resetForm()
                }
              }}
              className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              <X className="w-4 h-4" />
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Variables List */}
      <div className="space-y-2">
        {variables.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No variables defined. Add one to get started.
          </div>
        ) : (
          variables.map((variable) => (
            <div
              key={variable.id}
              className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <span className="font-mono font-medium">${variable.name}</span>
                  <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded">
                    {variable.value_type}
                  </span>
                  <span className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                    {variable.scope}
                  </span>
                  {variable.is_secret && (
                    <span className="px-2 py-1 text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded">
                      Secret
                    </span>
                  )}
                </div>
                <div className="mt-1 text-sm text-gray-600 dark:text-gray-400 font-mono">
                  {variable.is_secret && !revealedSecrets.has(variable.id)
                    ? '********'
                    : variable.value}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {variable.is_secret && (
                  <button
                    onClick={() => toggleSecretVisibility(variable.id)}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    title={revealedSecrets.has(variable.id) ? 'Hide' : 'Reveal'}
                  >
                    {revealedSecrets.has(variable.id) ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                )}
                <button
                  onClick={() => startEdit(variable)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="Edit"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(variable.id)}
                  className="p-2 hover:bg-red-100 dark:hover:bg-red-900 text-red-600 rounded-lg transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <h4 className="font-medium text-sm mb-2">Using Variables</h4>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Reference variables in your workflow using the syntax: <code className="px-1 py-0.5 bg-white dark:bg-gray-800 rounded">{'${variable_name}'}</code>
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Example: <code className="px-1 py-0.5 bg-white dark:bg-gray-800 rounded">{'${api_key}'}</code> or <code className="px-1 py-0.5 bg-white dark:bg-gray-800 rounded">{'${base_url}'}</code>
        </p>
      </div>
    </div>
  )
}
