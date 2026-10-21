import { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'
import clsx from 'clsx'
import { Icons } from './icons'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

/** Chat ichidagi animatsiyali nuqta. */
function LoadingDot() {
  return (
    <svg className="h-1.5 w-1.5 animate-bounce" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="1" />
    </svg>
  )
}

export function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState<Array<{ role: string; parts: string[] }>>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
    }
  }, [isOpen])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])

    try {
      const response = await api.post<{ response: string; history: Array<{ role: string; parts: string[] }> }>(
        '/chatbot/',
        { message: userMessage, history }
      )

      setMessages((prev) => [...prev, { role: 'assistant', content: response.data.response }])
      setHistory(response.data.history)
    } catch (error) {
      setMessages((prev) => [...prev, { role: 'assistant', content: "Xatolik yuz berdi. Qayta urinib ko'ring." }])
      console.error('Chatbot error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleChat = () => {
    setIsOpen((prev) => !prev)
    if (!isOpen && messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          content: "Salom! Men Kutubxona yordamchisiman. Sizga qanday yordam bera olaman?",
        },
      ])
    }
  }

  const clearChat = () => {
    setMessages([])
    setHistory([])
  }

  return (
    <>
      <button
        onClick={toggleChat}
        aria-label={isOpen ? "Chatni yopish" : "Chatni ochish"}
        className={clsx(
          'fixed bottom-6 right-6 z-50 rounded-full p-3 shadow-lg transition-all duration-300',
          'bg-brand-600 text-white hover:bg-brand-700',
          isOpen && 'rotate-45 bg-red-500 hover:bg-red-600',
          'dark:bg-brand-500 dark:hover:bg-brand-600'
        )}
      >
        {isOpen ? <Icons.close className='h-6 w-6' /> : <Icons.chat className='h-6 w-6' />}
      </button>

      {isOpen && (
        <div className="fixed bottom-6 right-6 z-40 w-full max-w-sm lg:max-w-md">
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white shadow-xl overflow-hidden dark:border-slate-700 dark:bg-slate-800">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-brand-100 p-2 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
                  <Icons.bot className='h-5 w-5' />
                </span>
                <span className="font-semibold text-slate-900 dark:text-slate-100">Kutubxona Asistani</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={clearChat}
                  aria-label="Chatni tozalash"
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                  title="Tozalash"
                >
                  <Icons.trash className='h-5 w-5' />
                </button>
                <button
                  onClick={toggleChat}
                  aria-label="Chatni yopish"
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  <Icons.close className='h-6 w-6' />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[400px]">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    'flex gap-3',
                    msg.role === 'user' && 'flex-row-reverse'
                  )}
                >
                  <div
                    className={clsx(
                      'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm',
                      msg.role === 'user'
                        ? 'bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                    )}
                  >
                    {msg.role === 'user' ? <Icons.user className='h-5 w-5' /> : <Icons.bot className='h-5 w-5' />}
                  </div>
                  <div
                    className={clsx(
                      'max-w-[75%] rounded-2xl px-4 py-2 text-sm',
                      msg.role === 'user'
                        ? 'bg-brand-600 text-white rounded-tr-sm'
                        : 'bg-slate-100 text-slate-900 rounded-tl-sm dark:bg-slate-700 dark:text-slate-100'
                    )}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center dark:bg-slate-700">
                    <Icons.bot className='h-5 w-5' />
                  </div>
                  <div className="bg-slate-100 rounded-2xl rounded-tl-sm px-4 py-2 text-sm dark:bg-slate-700">
                    <div className="flex gap-1">
                      <LoadingDot />
                      <span style={{ animationDelay: '0.1s' }}><LoadingDot /></span>
                      <span style={{ animationDelay: '0.2s' }}><LoadingDot /></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} className="border-t border-slate-200 p-3 dark:border-slate-700">
              <div className="flex gap-2">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Xabar yozing..."
                  rows={1}
                  disabled={isLoading}
                  className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                  aria-label="Xabar matni"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className={clsx(
                    'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                    'bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed',
                    'dark:bg-brand-500 dark:hover:bg-brand-600'
                  )}
                  aria-label="Yuborish"
                >
                  <Icons.send className='h-5 w-5' />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}