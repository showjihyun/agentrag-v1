"use client"

import { useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { XCircle } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function OAuthErrorPage() {
  const searchParams = useSearchParams()
  const error = searchParams.get("error")
  const description = searchParams.get("description")

  const handleClose = () => {
    window.close()
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-[400px]">
        <CardHeader>
          <div className="flex items-center gap-2">
            <XCircle className="h-6 w-6 text-red-500" />
            <CardTitle>Authentication Failed</CardTitle>
          </div>
          <CardDescription>
            {description || "An error occurred during authentication"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <p className="text-sm text-muted-foreground mb-4">
              Error code: {error}
            </p>
          )}
          <Button onClick={handleClose} className="w-full">
            Close Window
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
