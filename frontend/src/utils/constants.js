export const PLATFORMS = [
  { id: 'avito',      name: 'Avito.ma',   icon: '🇲🇦' },
  { id: 'jumia',      name: 'Jumia',      icon: '🛒' },
  { id: 'aliexpress', name: 'AliExpress', icon: '🌏' },
  { id: 'amazon',     name: 'Amazon',     icon: '📦' },
  { id: 'ebay',       name: 'eBay',       icon: '🏷️' },
]

export const STATUS_COLORS = {
  pending:    'warning',
  processing: 'info',
  completed:  'success',
  failed:     'danger',
}

export const STATUS_LABELS = {
  pending:    'Pending',
  processing: 'Processing',
  completed:  'Completed',
  failed:     'Failed',
}

export const CONDITION_LABELS = {
  new:      'New',
  like_new: 'Like New',
  good:     'Good',
  fair:     'Fair',
  used:     'Used',
}

export const SORT_OPTIONS = [
  { value: 'price_asc',   label: 'Price ↑ (Low to High)' },
  { value: 'price_desc',  label: 'Price ↓ (High to Low)' },
  { value: 'deal_desc',   label: 'Best Deal ↓' },
  { value: 'default',     label: 'Default' },
]

export const CLUSTER_COLORS = [
  '#6366f1', '#06b6d4', '#10b981', '#f59e0b',
  '#ec4899', '#8b5cf6', '#f97316', '#14b8a6',
]

export const PAGE_SIZE = 20
