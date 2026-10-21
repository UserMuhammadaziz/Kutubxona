import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import rehypeSlug from 'rehype-slug'
import remarkGfm from 'remark-gfm'
import qollanma from '../../../QOLLANMA.md?raw'
import { Card, PageHeader } from '../components/ui'

const components: Components = {
  h1: ({ node: _node, children, ...props }) => (
    <h1
      {...props}
      className="mb-5 mt-2 border-b border-slate-200 pb-3 text-2xl font-bold text-slate-900 first:mt-0 dark:border-slate-700 dark:text-slate-100"
    >
      {children}
    </h1>
  ),
  h2: ({ node: _node, children, ...props }) => (
    <h2
      {...props}
      className="mb-3 mt-8 scroll-mt-6 border-b border-slate-100 pb-2 text-xl font-semibold text-slate-900 dark:border-slate-700/60 dark:text-slate-100"
    >
      {children}
    </h2>
  ),
  h3: ({ node: _node, children, ...props }) => (
    <h3 {...props} className="mb-2 mt-6 scroll-mt-6 text-lg font-semibold text-slate-900 dark:text-slate-100">
      {children}
    </h3>
  ),
  h4: ({ node: _node, children, ...props }) => (
    <h4 {...props} className="mb-2 mt-5 scroll-mt-6 text-base font-semibold text-slate-800 dark:text-slate-200">
      {children}
    </h4>
  ),
  p: ({ node: _node, children, ...props }) => (
    <p {...props} className="my-3 leading-7 text-slate-700 dark:text-slate-300">
      {children}
    </p>
  ),
  a: ({ node: _node, children, href, ...props }) => {
    const tashqi = /^https?:\/\//.test(href || '')
    return (
      <a
        {...props}
        href={href}
        {...(tashqi ? { target: '_blank', rel: 'noreferrer' } : {})}
        className="font-medium text-brand-600 underline underline-offset-2 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
      >
        {children}
      </a>
    )
  },
  ul: ({ node: _node, children, ...props }) => (
    <ul {...props} className="my-3 list-disc space-y-1.5 pl-6 text-slate-700 dark:text-slate-300">
      {children}
    </ul>
  ),
  ol: ({ node: _node, children, ...props }) => (
    <ol {...props} className="my-3 list-decimal space-y-1.5 pl-6 text-slate-700 dark:text-slate-300">
      {children}
    </ol>
  ),
  li: ({ node: _node, children, ...props }) => (
    <li {...props} className="leading-7 [&>ul]:my-1 [&>ol]:my-1">
      {children}
    </li>
  ),
  blockquote: ({ node: _node, children, ...props }) => (
    <blockquote
      {...props}
      className="my-4 rounded-r-lg border-l-4 border-brand-400 bg-brand-50/60 px-4 py-3 text-sm text-slate-700 dark:border-brand-500 dark:bg-brand-900/20 dark:text-slate-300"
    >
      {children}
    </blockquote>
  ),
  hr: () => (
    <hr className="my-8 border-slate-200 dark:border-slate-700" />
  ),
  strong: ({ node: _node, children, ...props }) => (
    <strong {...props} className="font-semibold text-slate-900 dark:text-slate-100">
      {children}
    </strong>
  ),
  code: ({ node: _node, className, children, ...props }) => {
    if (typeof className === 'string' && className.includes('language-')) {
      return (
        <code {...props} className={className}>
          {children}
        </code>
      )
    }
    return (
      <code
        {...props}
        className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[0.85em] text-rose-700 dark:bg-slate-700 dark:text-rose-300"
      >
        {children}
      </code>
    )
  },
  pre: ({ node: _node, children, ...props }) => (
    <pre
      {...props}
      className="my-4 overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm leading-6 text-slate-100 [&>code]:bg-transparent [&>code]:p-0 [&>code]:font-mono [&>code]:text-inherit"
    >
      {children}
    </pre>
  ),
  table: ({ node: _node, children, ...props }) => (
    <div className="my-4 overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
      <table {...props} className="w-full border-collapse text-sm">
        {children}
      </table>
    </div>
  ),
  thead: ({ node: _node, children, ...props }) => (
    <thead {...props} className="bg-canvas dark:bg-slate-800/60">
      {children}
    </thead>
  ),
  th: ({ node: _node, children, ...props }) => (
    <th
      {...props}
      className="border-b border-slate-200 px-3 py-2.5 text-left font-semibold text-slate-600 dark:border-slate-700 dark:text-slate-300"
    >
      {children}
    </th>
  ),
  td: ({ node: _node, children, ...props }) => (
    <td
      {...props}
      className="border-b border-slate-100 px-3 py-2.5 align-top text-slate-700 last:border-0 dark:border-slate-700/60 dark:text-slate-300"
    >
      {children}
    </td>
  ),
}

export function Guide() {
  return (
    <div>
      <PageHeader
        title="Qo'llanma"
        subtitle="Saytdan foydalanish, API va bot bo'yicha to'liq qo'llanma"
      />
      <Card className="p-4 sm:p-6 lg:p-8">
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSlug]} components={components}>
          {qollanma}
        </ReactMarkdown>
      </Card>
    </div>
  )
}
