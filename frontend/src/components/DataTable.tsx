import { useMemo, useState, type ReactNode } from 'react'
import { createTheme, ThemeProvider } from '@mui/material/styles'
import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TablePagination from '@mui/material/TablePagination'
import TableRow from '@mui/material/TableRow'
import TableSortLabel from '@mui/material/TableSortLabel'
import { useThemeStore } from '../store/theme'

// ============================================================================
// MUI Data Table  (https://mui.com/material-ui/react-table/#data-table)
// Saralash (sort) + sahifalash (pagination) + sticky headerga ega umumiy jadval.
// Server-side sahifalash: `pagination` prop berilsa (count/page/rowsPerPage),
// aks holda joriy ro'yxatni klient tomonda sahifalaydi.
// ============================================================================

export interface DataTableColumn<T> {
  id: string
  label: string
  numeric?: boolean
  sortable?: boolean
  align?: 'left' | 'right' | 'center'
  render?: (row: T) => ReactNode
  /** Qiyoslashda ishlatiladigan asl qiymat (ko'rinish emas) */
  sortBy?: (row: T) => string | number
}

export interface ServerPagination {
  /** Umumiy yozuvlar soni */
  count: number
  /** 0-boshlang'ich */
  page: number
  rowsPerPage: number
  onPageChange: (page: number) => void
  onRowsPerPageChange?: (rows: number) => void
}

interface DataTableProps<T> {
  data: T[]
  columns: DataTableColumn<T>[]
  getRowId: (row: T) => string | number
  pagination?: ServerPagination
  pageSizes?: number[]
  onRowClick?: (row: T) => void
  rowClassName?: (row: T) => string
  emptyText?: string
}

// ---- Saralash --------------------------------------------------------------
type Order = 'asc' | 'desc'

function sortComparator<T>(a: T, b: T, col: DataTableColumn<T>): number {
  const av = col.sortBy ? col.sortBy(a) : ((a as unknown as Record<string, unknown>)[col.id] ?? '')
  const bv = col.sortBy ? col.sortBy(b) : ((b as unknown as Record<string, unknown>)[col.id] ?? '')
  if (typeof av === 'number' && typeof bv === 'number') return av - bv
  return String(av).localeCompare(String(bv), 'uz')
}

function getSortedRows<T>(rows: T[], cols: DataTableColumn<T>[], orderBy: string | null, order: Order | null): T[] {
  if (!order || !orderBy) return rows
  const col = cols.find((c) => c.id === orderBy)
  if (!col) return rows
  const signed = (a: T, b: T) => (order === 'desc' ? -1 : 1) * sortComparator(a, b, col)
  return [...rows].sort(signed)
}

// ---- Mavzu (light/dark — app theme store bilan sinxron) --------------------
function buildDataTableTheme(dark: boolean) {
  return createTheme({
    palette: {
      mode: dark ? 'dark' : 'light',
      primary: { main: dark ? '#38bdf8' : '#0f172a' },
      background: { paper: dark ? '#1e293b' : '#ffffff' },
      text: dark
        ? { primary: '#e2e8f0', secondary: '#94a3b8' }
        : { primary: '#0f172a', secondary: '#64748b' },
    },
    typography: { fontFamily: 'inherit' },
    components: {
      MuiTableCell: {
        styleOverrides: {
          root: {
            padding: '11px 16px',
            borderColor: dark ? '#334155' : '#e2e8f0',
            whiteSpace: 'nowrap',
          },
          head: {
            fontWeight: 600,
            fontSize: 11,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            color: dark ? '#94a3b8' : '#64748b',
            userSelect: 'none',
          },
        },
      },
    },
  })
}

export function DataTable<T>({
  data,
  columns,
  getRowId,
  pagination,
  pageSizes = [10, 20, 50],
  onRowClick,
  rowClassName,
  emptyText = "Ma'lumot topilmadi",
}: DataTableProps<T>) {
  const appTheme = useThemeStore((s) => s.theme)
  const dark = appTheme === 'dark'
  const muiTheme = useMemo(() => buildDataTableTheme(dark), [dark])

  const [order, setOrder] = useState<Order | null>(null)
  const [orderBy, setOrderBy] = useState<string | null>(null)
  const [clientPage, setClientPage] = useState(0)
  const [clientRowsPerPage, setClientRowsPerPage] = useState(pageSizes[0])

  const handleRequestSort = (_e: unknown, id: string) => {
    // Bir ustunda: asc -> desc -> asc ... (keyingi ustunga o'tilsa yana asc)
    if (orderBy === id) {
      setOrder(order === 'asc' ? 'desc' : 'asc')
    } else {
      setOrder('asc')
      setOrderBy(id)
    }
  }

  const sorted = useMemo(() => getSortedRows(data, columns, orderBy, order), [data, columns, orderBy, order])

  const visibleRows = useMemo(() => {
    if (pagination) return sorted
    const start = clientPage * clientRowsPerPage
    return sorted.slice(start, start + clientRowsPerPage)
  }, [sorted, pagination, clientPage, clientRowsPerPage])

  return (
    <ThemeProvider theme={muiTheme}>
      <Paper
      component={TableContainer}
      sx={{
        borderRadius: '0.75rem',
        border: '1px solid',
        borderColor: dark ? '#334155' : '#e2e8f0',
        overflow: 'auto',
        bgcolor: dark ? 'rgba(30,41,59,0.4)' : 'transparent',
        '& .MuiTable-root': { minWidth: 560 },
      }}
    >
      <Table stickyHeader aria-label="data table">
        <TableHead>
          <TableRow>
            {columns.map((col) => (
              <TableCell
                key={col.id}
                align={col.align ?? (col.numeric ? 'right' : 'left')}
                sortDirection={orderBy === col.id && order !== null ? order : false}
                sx={{ bgcolor: dark ? '#1e293bee' : '#f1f5f9ee', backdropFilter: 'blur(6px)' }}
              >
                {col.sortable === false ? (
                  col.label
                ) : (
                  <TableSortLabel
                    active={orderBy === col.id}
                    direction={orderBy === col.id ? order! : 'asc'}
                    onClick={(e) => handleRequestSort(e, col.id)}
                  >
                    {col.label}
                  </TableSortLabel>
                )}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {visibleRows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} align="center" sx={{ py: 6, color: '#94a3b8' }}>
                {emptyText}
              </TableCell>
            </TableRow>
          ) : (
            visibleRows.map((row) => {
              const id = getRowId(row)
              return (
                <TableRow
                  key={id}
                  hover={!!onRowClick}
                  className={rowClassName?.(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                >
                  {columns.map((col) => (
                    <TableCell key={col.id} align={col.align ?? (col.numeric ? 'right' : 'left')}>
                      {col.render ? col.render(row) : String((row as unknown as Record<string, unknown>)[col.id] ?? '—')}
                    </TableCell>
                  ))}
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>
      <TablePagination
        component="div"
        count={pagination ? pagination.count : sorted.length}
        page={pagination ? pagination.page : clientPage}
        onPageChange={(_, p) =>
          pagination ? pagination.onPageChange(p) : setClientPage(p)
        }
        rowsPerPageOptions={pageSizes}
        rowsPerPage={pagination ? pagination.rowsPerPage : clientRowsPerPage}
        onRowsPerPageChange={(e) => {
          const rows = parseInt(e.target.value, 10)
          setClientPage(0)
          if (pagination) pagination.onRowsPerPageChange?.(rows)
          else setClientRowsPerPage(rows)
        }}
        labelRowsPerPage="Sahifada:"
        labelDisplayedRows={({ from, to, count }) => `${from}–${to} / ${count !== -1 ? count : `${to}+`}`}
      />
      </Paper>
    </ThemeProvider>
  )
}

export default DataTable
