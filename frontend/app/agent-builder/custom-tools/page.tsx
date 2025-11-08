"use client";

import { useState } from "react";
import { CustomToolManager } from "@/components/agent-builder/custom-tools/CustomToolManager";
import { ToolMarketplace } from "@/components/agent-builder/custom-tools/ToolMarketplace";
import { Button } from "@/components/ui/button";

export default function CustomToolsPage() {
  const [activeTab, setActiveTab] = useState<"my-tools" | "marketplace">(
    "my-tools"
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant={activeTab === "my-tools" ? "default" : "ghost"}
              onClick={() => setActiveTab("my-tools")}
            >
              My Tools
            </Button>
            <Button
              variant={activeTab === "marketplace" ? "default" : "ghost"}
              onClick={() => setActiveTab("marketplace")}
            >
              Marketplace
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto">
        {activeTab === "my-tools" ? (
          <CustomToolManager />
        ) : (
          <ToolMarketplace />
        )}
      </div>
    </div>
  );
}
