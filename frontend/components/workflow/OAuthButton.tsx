"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, XCircle, Loader2 } from "lucide-react"

interface OAuthButtonProps {
  toolId: string
  toolName: string
  onAuthSuccess?: () => void
}

export function OAuthButton({ toolId, toolName, onAuthSuccess }: OAuthButtonProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [expiresAt, setExpiresAt] = useState<string | null>(null)

  useEffect(() => {
    checkAuthStatus()
  }, [toolId])

  const checkAuthStatus = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`/api/agent-builder/oauth/status/${toolId}`, {
        credentials: "include"
      })

      if (response.ok) {
        const data = await response.json()
        setIsAuthenticated(data.is_authenticated)
        setExpiresAt(data.expires_at)
      }
    } catch (error) {
      console.error("Failed to check OAuth status:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAuthenticate = async () => {
    try {
      setIsLoading(true)

      // Get redirect URI (current page)
      const redirectUri = `${window.location.origin}/api/agent-builder/oauth/callback`

      // Initiate OAuth flow
      const response = await fetch("/api/agent-builder/oauth/init", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({
          tool_id: toolId,
          redirect_uri: redirectUri
        })
      })

      if (!response.ok) {
        throw new Error("Failed to initiate OAuth flow")
      }

      const data = await response.json()

      // Open OAuth authorization URL in popup
      const width = 600
      const height = 700
      const left = window.screen.width / 2 - width / 2
      const top = window.screen.height / 2 - height / 2

      const popup = window.open(
        data.auth_url,
        "oauth_popup",
        `width=${width},height=${height},left=${left},top=${top}`
      )

      // Poll for popup closure
      const pollTimer = setInterval(() => {
        if (popup?.closed) {
          clearInterval(pollTimer)
          // Check auth status after popup closes
          setTimeout(() => {
            checkAuthStatus()
            onAuthSuccess?.()
          }, 1000)
        }
      }, 500)
    } catch (error) {
      console.error("OAuth authentication failed:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRevoke = async () => {
    try {
      setIsLoading(true)

      const response = await fetch(`/api/agent-builder/oauth/revoke/${toolId}`, {
        method: "DELETE",
        credentials: "include"
      })

      if (response.ok) {
        setIsAuthenticated(false)
        setExpiresAt(null)
      }
    } catch (error) {
      console.error("Failed to revoke OAuth credentials:", error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Checking status...</span>
      </div>
    )
  }

  if (isAuthenticated) {
    return (
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="gap-1">
          <CheckCircle2 className="h-3 w-3 text-green-500" />
          Connected
        </Badge>
        {expiresAt && (
          <span className="text-xs text-muted-foreground">
            Expires: {new Date(expiresAt).toLocaleDateString()}
          </span>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRevoke}
          disabled={isLoading}
        >
          Disconnect
        </Button>
      </div>
    )
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleAuthenticate}
      disabled={isLoading}
      className="gap-2"
    >
      <XCircle className="h-4 w-4 text-orange-500" />
      Connect {toolName}
    </Button>
  )
}
