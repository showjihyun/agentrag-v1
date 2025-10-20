import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Middleware for protecting routes that require authentication.
 * 
 * This runs before every request and checks if the user is authenticated
 * for protected routes.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Get auth token from cookies
  const token = request.cookies.get('auth_token')?.value

  // Define protected routes
  const protectedRoutes = [
    '/dashboard',
    '/api/documents',
    '/api/conversations',
  ]

  // Define auth routes (redirect to home if already authenticated)
  const authRoutes = [
    '/auth/login',
    '/auth/register',
  ]

  // Check if current path is protected
  const isProtectedRoute = protectedRoutes.some(route =>
    pathname.startsWith(route)
  )

  // Check if current path is auth route
  const isAuthRoute = authRoutes.some(route =>
    pathname.startsWith(route)
  )

  // Redirect to login if accessing protected route without token
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Redirect to home if accessing auth route with valid token
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

/**
 * Configure which routes the middleware should run on.
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
