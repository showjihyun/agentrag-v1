"use client";

import React, { useState, useEffect } from "react";
import { Search, Star, Download, Filter, TrendingUp, Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { agentBuilderApi } from "@/lib/api/agent-builder";

interface MarketplaceAgent {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  category: string;
  rating: number;
  rating_count: number;
  install_count: number;
  author: string;
  tags: string[];
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export default function MarketplacePage() {
  const [agents, setAgents] = useState<MarketplaceAgent[]>([]);
  const [filteredAgents, setFilteredAgents] = useState<MarketplaceAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [sortBy, setSortBy] = useState("popular");
  const { toast } = useToast();

  useEffect(() => {
    loadMarketplaceAgents();
  }, []);

  useEffect(() => {
    filterAndSortAgents();
  }, [agents, searchQuery, categoryFilter, sortBy]);

  const loadMarketplaceAgents = async () => {
    try {
      setLoading(true);
      // Fetch public agents from marketplace
      const response = await agentBuilderApi.listAgents({ is_public: true });
      setAgents(response);
    } catch (error) {
      console.error("Failed to load marketplace agents:", error);
      toast({
        title: "Error",
        description: "Failed to load marketplace agents",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortAgents = () => {
    let filtered = [...agents];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (agent) =>
          agent.name.toLowerCase().includes(query) ||
          agent.description?.toLowerCase().includes(query) ||
          agent.tags?.some((tag) => tag.toLowerCase().includes(query))
      );
    }

    // Apply category filter
    if (categoryFilter !== "all") {
      filtered = filtered.filter((agent) => agent.category === categoryFilter);
    }

    // Apply sorting
    switch (sortBy) {
      case "popular":
        filtered.sort((a, b) => (b.install_count || 0) - (a.install_count || 0));
        break;
      case "rating":
        filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));
        break;
      case "recent":
        filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case "name":
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
    }

    setFilteredAgents(filtered);
  };

  const handleInstallAgent = async (agentId: string) => {
    try {
      // Clone agent from marketplace
      await agentBuilderApi.cloneAgent(agentId);
      
      toast({
        title: "Success",
        description: "Agent installed successfully",
      });
    } catch (error) {
      console.error("Failed to install agent:", error);
      toast({
        title: "Error",
        description: "Failed to install agent",
        variant: "destructive",
      });
    }
  };

  const categories = [
    { value: "all", label: "All Categories" },
    { value: "research", label: "Research" },
    { value: "data-analysis", label: "Data Analysis" },
    { value: "content", label: "Content Generation" },
    { value: "automation", label: "Automation" },
    { value: "customer-service", label: "Customer Service" },
    { value: "other", label: "Other" },
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Agent Marketplace</h1>
        <p className="text-muted-foreground">
          Discover and install pre-built agents from the community
        </p>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full md:w-[200px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((cat) => (
              <SelectItem key={cat.value} value={cat.value}>
                {cat.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-full md:w-[200px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="popular">Most Popular</SelectItem>
            <SelectItem value="rating">Highest Rated</SelectItem>
            <SelectItem value="recent">Most Recent</SelectItem>
            <SelectItem value="name">Name (A-Z)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
            <Filter className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(agents.map((a) => a.category)).size}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Installs</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {agents.reduce((sum, a) => sum + (a.install_count || 0), 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Grid */}
      <ScrollArea className="h-[600px]">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-full mt-2" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-20 w-full" />
                </CardContent>
                <CardFooter>
                  <Skeleton className="h-10 w-full" />
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : filteredAgents.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No agents found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAgents.map((agent) => (
              <Card key={agent.id} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{agent.name}</CardTitle>
                      <CardDescription className="mt-1">
                        by {agent.author || "Unknown"}
                      </CardDescription>
                    </div>
                    {agent.rating > 0 && (
                      <div className="flex items-center gap-1">
                        <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="text-sm font-medium">{agent.rating.toFixed(1)}</span>
                        <span className="text-xs text-muted-foreground">
                          ({agent.rating_count})
                        </span>
                      </div>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="flex-1">
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {agent.description || "No description available"}
                  </p>

                  <div className="flex flex-wrap gap-2 mt-4">
                    {agent.category && (
                      <Badge variant="secondary">{agent.category}</Badge>
                    )}
                    {agent.tags?.slice(0, 2).map((tag) => (
                      <Badge key={tag} variant="outline">
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Download className="h-4 w-4" />
                      <span>{agent.install_count || 0}</span>
                    </div>
                  </div>
                </CardContent>

                <CardFooter>
                  <Button
                    className="w-full"
                    onClick={() => handleInstallAgent(agent.id)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Install Agent
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
