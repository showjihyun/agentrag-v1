"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Search,
  Star,
  Download,
  TrendingUp,
  Eye,
  MessageSquare,
} from "lucide-react";

interface MarketplaceTool {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  usage_count: number;
  avg_rating: number;
  rating_count: number;
  created_at: string;
}

interface ToolRating {
  id: string;
  rating: number;
  review: string;
  user: {
    id: string;
    username: string;
  };
  created_at: string;
}

export function ToolMarketplace() {
  const [tools, setTools] = useState<MarketplaceTool[]>([]);
  const [filteredTools, setFilteredTools] = useState<MarketplaceTool[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [toolRatings, setToolRatings] = useState<ToolRating[]>([]);
  const [userRating, setUserRating] = useState(0);
  const [userReview, setUserReview] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFeaturedTools();
  }, []);

  useEffect(() => {
    filterTools();
  }, [searchQuery, tools]);

  const loadFeaturedTools = async () => {
    try {
      const response = await fetch(
        "/api/agent-builder/custom-tools/marketplace/featured"
      );
      const data = await response.json();
      setTools(data.tools || []);
    } catch (error) {
      console.error("Failed to load featured tools:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterTools = () => {
    if (!searchQuery) {
      setFilteredTools(tools);
      return;
    }

    const filtered = tools.filter(
      (tool) =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    setFilteredTools(filtered);
  };

  const loadToolRatings = async (toolId: string) => {
    try {
      const response = await fetch(
        `/api/agent-builder/custom-tools/${toolId}/ratings`
      );
      const data = await response.json();
      setToolRatings(data.ratings || []);
    } catch (error) {
      console.error("Failed to load ratings:", error);
    }
  };

  const handleViewTool = (toolId: string) => {
    setSelectedTool(toolId);
    loadToolRatings(toolId);
  };

  const handleCloneTool = async (toolId: string) => {
    try {
      const response = await fetch(
        `/api/agent-builder/custom-tools/${toolId}/clone`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        alert("Tool cloned successfully!");
      }
    } catch (error) {
      console.error("Failed to clone tool:", error);
    }
  };

  const handleRateTool = async (toolId: string) => {
    if (userRating === 0) {
      alert("Please select a rating");
      return;
    }

    try {
      const response = await fetch(
        `/api/agent-builder/custom-tools/${toolId}/rate?rating=${userRating}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ review: userReview }),
        }
      );

      if (response.ok) {
        setUserRating(0);
        setUserReview("");
        loadToolRatings(toolId);
        loadFeaturedTools();
      }
    } catch (error) {
      console.error("Failed to rate tool:", error);
    }
  };

  const renderStars = (rating: number, interactive: boolean = false) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 ${
              star <= rating
                ? "text-yellow-500 fill-yellow-500"
                : "text-gray-300"
            } ${interactive ? "cursor-pointer" : ""}`}
            onClick={
              interactive ? () => setUserRating(star) : undefined
            }
          />
        ))}
      </div>
    );
  };

  if (selectedTool) {
    const tool = tools.find((t) => t.id === selectedTool);
    if (!tool) return null;

    return (
      <div className="p-6 space-y-6">
        <Button
          onClick={() => setSelectedTool(null)}
          variant="outline"
          size="sm"
        >
          ← Back to Marketplace
        </Button>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <span className="text-5xl">{tool.icon}</span>
                <div>
                  <CardTitle className="text-2xl">{tool.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {tool.category}
                  </p>
                  <div className="flex items-center gap-4 mt-2">
                    <div className="flex items-center gap-1">
                      {renderStars(Math.round(tool.avg_rating))}
                      <span className="text-sm text-muted-foreground ml-1">
                        ({tool.rating_count})
                      </span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {tool.usage_count} uses
                    </span>
                  </div>
                </div>
              </div>
              <Button onClick={() => handleCloneTool(tool.id)}>
                <Download className="h-4 w-4 mr-2" />
                Add to My Tools
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">Description</h3>
              <p className="text-muted-foreground">{tool.description}</p>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Rate this Tool</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">
                    Your Rating
                  </label>
                  {renderStars(userRating, true)}
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">
                    Review (optional)
                  </label>
                  <textarea
                    value={userReview}
                    onChange={(e) => setUserReview(e.target.value)}
                    className="w-full p-3 border rounded-md"
                    rows={3}
                    placeholder="Share your experience with this tool..."
                  />
                </div>
                <Button onClick={() => handleRateTool(tool.id)}>
                  Submit Rating
                </Button>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-4">
                Reviews ({toolRatings.length})
              </h3>
              <div className="space-y-4">
                {toolRatings.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No reviews yet. Be the first to review!
                  </p>
                ) : (
                  toolRatings.map((rating) => (
                    <Card key={rating.id}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-medium">
                              {rating.user.username}
                            </p>
                            {renderStars(rating.rating)}
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {new Date(rating.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {rating.review && (
                          <p className="text-sm text-muted-foreground">
                            {rating.review}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Tool Marketplace</h2>
        <p className="text-muted-foreground">
          Discover and use tools created by the community
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search marketplace..."
          className="pl-10"
        />
      </div>

      {loading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading marketplace...</p>
        </div>
      ) : filteredTools.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              No tools found in marketplace
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map((tool) => (
            <Card
              key={tool.id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleViewTool(tool.id)}
            >
              <CardHeader>
                <div className="flex items-start gap-3">
                  <span className="text-3xl">{tool.icon}</span>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{tool.name}</CardTitle>
                    <p className="text-xs text-muted-foreground">
                      {tool.category}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {tool.description}
                </p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    {renderStars(Math.round(tool.avg_rating))}
                    <span className="text-xs text-muted-foreground ml-1">
                      ({tool.rating_count})
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      {tool.usage_count}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
