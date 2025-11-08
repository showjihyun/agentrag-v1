"use client"

import { useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { CheckCircle2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function OAuthSuccessPage() {
  const searchParams = useSearchParams()
  const toolId = searchParams.get("tool_id")

  useEffect(() => {
    // Close window after 2 seconds
    const timer = setTimeout(() => {
      window.close()
    }, 2000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-[400px]">
        <CardHeader>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-6 w-6 text-green-500" />
            <CardTitle>Authentication Successful</CardTitle>
          </div>
          <CardDescription>
            You have successfully connected {toolId}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            This window will close automatically...
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
