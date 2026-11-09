import api from './api'

export async function generateAndDownloadDossier(investigationId) {
  await api.post(`/dossier/${investigationId}/generate`)
  const response = await api.get(`/dossier/${investigationId}/download`, {
    responseType: 'blob',
  })

  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = `Investigation_Dossier_${investigationId}.pdf`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
