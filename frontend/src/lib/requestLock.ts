/**
 * While the selected library is not active the server refuses every tenant request,
 * so the client does not send them at all. Only the paths below stay open.
 */
const OPEN_PATHS =
  /^\/(auth\/(token|register|me|organization|memberships)|issue-reports|push)\//
/** Platform users keep managing organizations and their own account. */
const PLATFORM_PATHS = /^\/(saas|auth)\//

let locked = false
let platformUser = false
let controller = new AbortController()

export function setRequestLock(next: { locked: boolean; platformUser: boolean }): void {
  platformUser = next.platformUser
  if (next.locked === locked) return
  locked = next.locked
  // Requests already on the way would only come back refused.
  if (locked) controller.abort()
  else controller = new AbortController()
}

export const isRequestLocked = () => locked

const isOpen = (url: string) => OPEN_PATHS.test(url) || (platformUser && PLATFORM_PATHS.test(url))

export const isRequestRefused = (url: string) => locked && !isOpen(url)

/** Abort signal for reads that must stop the moment the library is blocked. */
export const lockSignal = (url: string) => (isOpen(url) ? undefined : controller.signal)
