"""
Swarm Intelligence Orchestrator - 2025 Trend Pattern

Implements swarm-based coordination where agents behave like a collective intelligence,
sharing information and adapting behaviors based on collective feedback.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import json
import random
from dataclasses import dataclass, field

from ..base_orchestrator import BaseOrchestrator
from ....domain.entities.agent import Agent
from ....domain.entities.workflow import Workflow
from ....domain.value_objects.orchestration_config import OrchestrationConfig
from .....core.event_bus import EventBus

logger = logging.getLogger(__name__)

@dataclass
class SwarmAgent:
    """Individual agent in the swarm with local state and behaviors"""
    agent_id: str
    position: Dict[str, float] = field(default_factory=dict)  # Multi-dimensional position
    velocity: Dict[str, float] = field(default_factory=dict)  # Movement direction
    local_best: Dict[str, Any] = field(default_factory=dict)  # Personal best solution
    fitness: float = 0.0
    pheromone_trails: Dict[str, float] = field(default_factory=dict)  # Communication trails
    neighbors: Set[str] = field(default_factory=set)
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class SwarmState:
    """Global swarm state and collective intelligence"""
    global_best: Dict[str, Any] = field(default_factory=dict)
    global_fitness: float = 0.0
    pheromone_map: Dict[str, Dict[str, float]] = field(default_factory=dict)
    convergence_threshold: float = 0.01
    diversity_index: float = 1.0
    generation: int = 0
    collective_memory: List[Dict[str, Any]] = field(default_factory=list)

class SwarmOrchestrator(BaseOrchestrator):
    """
    Swarm Intelligence Orchestrator
    
    Coordinates agents using swarm intelligence principles:
    - Particle Swarm Optimization (PSO) for exploration
    - Ant Colony Optimization (ACO) for path finding
    - Collective decision making
    - Emergent behavior patterns
    """
    
    def __init__(self, config: OrchestrationConfig, event_bus: EventBus):
        super().__init__(config, event_bus)
        self.swarm_agents: Dict[str, SwarmAgent] = {}
        self.swarm_state = SwarmState()
        
        # Swarm parameters
        self.inertia_weight = config.get_parameter("inertia_weight", 0.7)
        self.cognitive_weight = config.get_parameter("cognitive_weight", 1.4)
        self.social_weight = config.get_parameter("social_weight", 1.4)
        self.pheromone_evaporation = config.get_parameter("pheromone_evaporation", 0.1)
        self.max_velocity = config.get_parameter("max_velocity", 1.0)
        self.neighborhood_size = config.get_parameter("neighborhood_size", 3)
        
        # Collective intelligence parameters
        self.memory_size = config.get_parameter("memory_size", 100)
        self.diversity_threshold = config.get_parameter("diversity_threshold", 0.3)
        self.adaptation_rate = config.get_parameter("adaptation_rate", 0.1)
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for swarm coordination"""
        self.event_bus.subscribe("agent_fitness_update", self._handle_fitness_update)
        self.event_bus.subscribe("pheromone_deposit", self._handle_pheromone_deposit)
        self.event_bus.subscribe("swarm_convergence", self._handle_convergence)
    
    async def orchestrate(self, workflow: Workflow, agents: List[Agent], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate agents using swarm intelligence
        
        Args:
            workflow: The workflow to execute
            agents: List of available agents
            context: Execution context
            
        Returns:
            Orchestration results with swarm metrics
        """
        try:
            logger.info(f"Starting swarm orchestration for workflow {workflow.id}")
            
            # Initialize swarm
            await self._initialize_swarm(agents, context)
            
            # Execute swarm iterations
            results = await self._execute_swarm_iterations(workflow, context)
            
            # Collect swarm intelligence
            swarm_intelligence = await self._collect_swarm_intelligence()
            
            return {
                "status": "completed",
                "results": results,
                "swarm_state": {
                    "generation": self.swarm_state.generation,
                    "global_fitness": self.swarm_state.global_fitness,
                    "diversity_index": self.swarm_state.diversity_index,
                    "convergence_achieved": self._check_convergence()
                },
                "collective_intelligence": swarm_intelligence,
                "execution_time": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Swarm orchestration failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "swarm_state": self._get_current_swarm_state()
            }
    
    async def _initialize_swarm(self, agents: List[Agent], context: Dict[str, Any]):
        """Initialize swarm agents with random positions and neighborhoods"""
        logger.info(f"Initializing swarm with {len(agents)} agents")
        
        # Create swarm agents
        for agent in agents:
            swarm_agent = SwarmAgent(
                agent_id=agent.id,
                position=self._generate_random_position(context),
                velocity=self._generate_random_velocity(),
                fitness=0.0
            )
            self.swarm_agents[agent.id] = swarm_agent
        
        # Establish neighborhoods
        await self._establish_neighborhoods()
        
        # Initialize pheromone map
        self._initialize_pheromone_map()
        
        await self.event_bus.publish("swarm_initialized", {
            "agent_count": len(agents),
            "neighborhoods": {aid: list(sa.neighbors) for aid, sa in self.swarm_agents.items()}
        })
    
    async def _execute_swarm_iterations(self, workflow: Workflow, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute swarm optimization iterations"""
        max_iterations = self.config.get_parameter("max_iterations", 50)
        results = {}
        
        for iteration in range(max_iterations):
            logger.info(f"Swarm iteration {iteration + 1}/{max_iterations}")
            
            # Update agent positions and velocities
            await self._update_swarm_positions()
            
            # Execute agents in parallel
            iteration_results = await self._execute_parallel_agents(workflow, context)
            
            # Update fitness values
            await self._update_fitness_values(iteration_results)
            
            # Update pheromone trails
            await self._update_pheromone_trails()
            
            # Check for convergence
            if self._check_convergence():
                logger.info(f"Swarm converged at iteration {iteration + 1}")
                break
            
            # Adapt swarm parameters
            await self._adapt_swarm_parameters()
            
            self.swarm_state.generation = iteration + 1
            results[f"iteration_{iteration + 1}"] = iteration_results
        
        return results
    
    async def _update_swarm_positions(self):
        """Update agent positions using PSO algorithm"""
        for agent_id, swarm_agent in self.swarm_agents.items():
            # Update velocity
            for dim in swarm_agent.position.keys():
                # Inertia component
                inertia = self.inertia_weight * swarm_agent.velocity.get(dim, 0)
                
                # Cognitive component (personal best)
                cognitive = (self.cognitive_weight * random.random() * 
                           (swarm_agent.local_best.get(dim, 0) - swarm_agent.position[dim]))
                
                # Social component (global best)
                social = (self.social_weight * random.random() * 
                         (self.swarm_state.global_best.get(dim, 0) - swarm_agent.position[dim]))
                
                # Update velocity with clamping
                new_velocity = inertia + cognitive + social
                swarm_agent.velocity[dim] = max(-self.max_velocity, 
                                              min(self.max_velocity, new_velocity))
                
                # Update position
                swarm_agent.position[dim] += swarm_agent.velocity[dim]
            
            swarm_agent.last_update = datetime.now()
    
    async def _execute_parallel_agents(self, workflow: Workflow, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents in parallel based on their swarm positions"""
        tasks = []
        
        for agent_id, swarm_agent in self.swarm_agents.items():
            # Create agent-specific context based on position
            agent_context = self._create_agent_context(swarm_agent, context)
            
            # Create execution task
            task = asyncio.create_task(
                self._execute_agent_with_swarm_context(agent_id, workflow, agent_context)
            )
            tasks.append((agent_id, task))
        
        # Wait for all agents to complete
        results = {}
        for agent_id, task in tasks:
            try:
                result = await task
                results[agent_id] = result
            except Exception as e:
                logger.error(f"Agent {agent_id} execution failed: {str(e)}")
                results[agent_id] = {"status": "failed", "error": str(e)}
        
        return results
    
    async def _execute_agent_with_swarm_context(self, agent_id: str, workflow: Workflow, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual agent with swarm-enhanced context"""
        swarm_agent = self.swarm_agents[agent_id]
        
        # Add swarm information to context
        context.update({
            "swarm_position": swarm_agent.position,
            "swarm_neighbors": list(swarm_agent.neighbors),
            "pheromone_trails": swarm_agent.pheromone_trails,
            "collective_memory": self.swarm_state.collective_memory[-10:]  # Recent memory
        })
        
        # Execute agent
        result = await self._execute_single_agent(agent_id, workflow, context)
        
        # Deposit pheromones based on result quality
        await self._deposit_pheromones(agent_id, result)
        
        return result
    
    async def _update_fitness_values(self, iteration_results: Dict[str, Any]):
        """Update fitness values for all swarm agents"""
        for agent_id, result in iteration_results.items():
            if agent_id in self.swarm_agents:
                swarm_agent = self.swarm_agents[agent_id]
                
                # Calculate fitness based on result quality
                fitness = self._calculate_fitness(result)
                swarm_agent.fitness = fitness
                
                # Update personal best
                if fitness > swarm_agent.local_best.get("fitness", 0):
                    swarm_agent.local_best = {
                        "fitness": fitness,
                        "position": swarm_agent.position.copy(),
                        "result": result
                    }
                
                # Update global best
                if fitness > self.swarm_state.global_fitness:
                    self.swarm_state.global_fitness = fitness
                    self.swarm_state.global_best = {
                        "fitness": fitness,
                        "position": swarm_agent.position.copy(),
                        "agent_id": agent_id,
                        "result": result
                    }
                
                await self.event_bus.publish("agent_fitness_update", {
                    "agent_id": agent_id,
                    "fitness": fitness,
                    "is_global_best": fitness == self.swarm_state.global_fitness
                })
    
    async def _update_pheromone_trails(self):
        """Update pheromone trails using ACO principles"""
        # Evaporate existing pheromones
        for path in self.swarm_state.pheromone_map:
            for target in self.swarm_state.pheromone_map[path]:
                self.swarm_state.pheromone_map[path][target] *= (1 - self.pheromone_evaporation)
        
        # Deposit new pheromones based on agent performance
        for agent_id, swarm_agent in self.swarm_agents.items():
            pheromone_strength = swarm_agent.fitness / max(self.swarm_state.global_fitness, 0.001)
            
            # Deposit pheromones on paths to neighbors
            for neighbor_id in swarm_agent.neighbors:
                path_key = f"{agent_id}->{neighbor_id}"
                if path_key not in self.swarm_state.pheromone_map:
                    self.swarm_state.pheromone_map[path_key] = {}
                
                self.swarm_state.pheromone_map[path_key]["strength"] = (
                    self.swarm_state.pheromone_map[path_key].get("strength", 0) + pheromone_strength
                )
    
    def _check_convergence(self) -> bool:
        """Check if swarm has converged"""
        if len(self.swarm_agents) < 2:
            return False
        
        # Calculate diversity index
        positions = [sa.position for sa in self.swarm_agents.values()]
        diversity = self._calculate_diversity(positions)
        self.swarm_state.diversity_index = diversity
        
        # Check convergence criteria
        return diversity < self.swarm_state.convergence_threshold
    
    async def _adapt_swarm_parameters(self):
        """Adapt swarm parameters based on current state"""
        # Adaptive inertia weight
        if self.swarm_state.diversity_index < self.diversity_threshold:
            # Increase exploration
            self.inertia_weight = min(0.9, self.inertia_weight + self.adaptation_rate)
        else:
            # Increase exploitation
            self.inertia_weight = max(0.4, self.inertia_weight - self.adaptation_rate)
        
        # Update collective memory
        if len(self.swarm_state.collective_memory) >= self.memory_size:
            self.swarm_state.collective_memory.pop(0)
        
        self.swarm_state.collective_memory.append({
            "generation": self.swarm_state.generation,
            "global_fitness": self.swarm_state.global_fitness,
            "diversity": self.swarm_state.diversity_index,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _collect_swarm_intelligence(self) -> Dict[str, Any]:
        """Collect and analyze swarm intelligence patterns"""
        return {
            "emergent_patterns": self._identify_emergent_patterns(),
            "collective_knowledge": self._extract_collective_knowledge(),
            "swarm_metrics": {
                "convergence_rate": self._calculate_convergence_rate(),
                "exploration_exploitation_ratio": self._calculate_ee_ratio(),
                "communication_efficiency": self._calculate_communication_efficiency()
            },
            "best_solutions": self._get_top_solutions(5)
        }
    
    def _generate_random_position(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Generate random position in solution space"""
        dimensions = context.get("solution_dimensions", ["quality", "speed", "cost"])
        return {dim: random.uniform(0, 1) for dim in dimensions}
    
    def _generate_random_velocity(self) -> Dict[str, float]:
        """Generate random initial velocity"""
        return {"quality": 0, "speed": 0, "cost": 0}
    
    async def _establish_neighborhoods(self):
        """Establish neighborhood relationships between agents"""
        agent_ids = list(self.swarm_agents.keys())
        
        for agent_id in agent_ids:
            # Random neighborhood selection
            available_neighbors = [aid for aid in agent_ids if aid != agent_id]
            neighbor_count = min(self.neighborhood_size, len(available_neighbors))
            neighbors = random.sample(available_neighbors, neighbor_count)
            
            self.swarm_agents[agent_id].neighbors = set(neighbors)
    
    def _initialize_pheromone_map(self):
        """Initialize pheromone trails between agents"""
        for agent_id, swarm_agent in self.swarm_agents.items():
            for neighbor_id in swarm_agent.neighbors:
                path_key = f"{agent_id}->{neighbor_id}"
                self.swarm_state.pheromone_map[path_key] = {"strength": 0.1}
    
    def _create_agent_context(self, swarm_agent: SwarmAgent, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create agent-specific context based on swarm position"""
        context = base_context.copy()
        
        # Add swarm-specific parameters
        context.update({
            "exploration_factor": swarm_agent.position.get("quality", 0.5),
            "speed_preference": swarm_agent.position.get("speed", 0.5),
            "cost_sensitivity": swarm_agent.position.get("cost", 0.5)
        })
        
        return context
    
    def _calculate_fitness(self, result: Dict[str, Any]) -> float:
        """Calculate fitness score for agent result"""
        if result.get("status") != "completed":
            return 0.0
        
        # Multi-objective fitness calculation
        quality_score = result.get("quality_score", 0.5)
        speed_score = 1.0 / max(result.get("execution_time", 1), 0.1)
        cost_score = 1.0 / max(result.get("resource_cost", 1), 0.1)
        
        # Weighted combination
        fitness = (0.4 * quality_score + 0.3 * speed_score + 0.3 * cost_score)
        return max(0, min(1, fitness))
    
    def _calculate_diversity(self, positions: List[Dict[str, float]]) -> float:
        """Calculate diversity index of swarm positions"""
        if len(positions) < 2:
            return 1.0
        
        total_distance = 0
        count = 0
        
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                distance = sum((positions[i].get(dim, 0) - positions[j].get(dim, 0)) ** 2 
                             for dim in positions[i].keys()) ** 0.5
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0
    
    def _identify_emergent_patterns(self) -> List[Dict[str, Any]]:
        """Identify emergent behavior patterns in the swarm"""
        patterns = []
        
        # Clustering pattern
        if self.swarm_state.diversity_index < 0.2:
            patterns.append({
                "type": "clustering",
                "description": "Agents are converging to similar solutions",
                "strength": 1 - self.swarm_state.diversity_index
            })
        
        # Leadership pattern
        best_agent_id = self.swarm_state.global_best.get("agent_id")
        if best_agent_id:
            patterns.append({
                "type": "leadership",
                "description": f"Agent {best_agent_id} is leading the swarm",
                "leader": best_agent_id,
                "fitness_gap": self.swarm_state.global_fitness - 
                              sum(sa.fitness for sa in self.swarm_agents.values()) / len(self.swarm_agents)
            })
        
        return patterns
    
    def _extract_collective_knowledge(self) -> Dict[str, Any]:
        """Extract collective knowledge from swarm memory"""
        if not self.swarm_state.collective_memory:
            return {}
        
        return {
            "learning_curve": [mem["global_fitness"] for mem in self.swarm_state.collective_memory],
            "diversity_evolution": [mem["diversity"] for mem in self.swarm_state.collective_memory],
            "convergence_points": [i for i, mem in enumerate(self.swarm_state.collective_memory) 
                                 if mem["diversity"] < self.swarm_state.convergence_threshold]
        }
    
    def _calculate_convergence_rate(self) -> float:
        """Calculate how quickly the swarm is converging"""
        if len(self.swarm_state.collective_memory) < 2:
            return 0.0
        
        recent_diversity = [mem["diversity"] for mem in self.swarm_state.collective_memory[-10:]]
        if len(recent_diversity) < 2:
            return 0.0
        
        return (recent_diversity[0] - recent_diversity[-1]) / len(recent_diversity)
    
    def _calculate_ee_ratio(self) -> float:
        """Calculate exploration vs exploitation ratio"""
        return self.swarm_state.diversity_index  # Higher diversity = more exploration
    
    def _calculate_communication_efficiency(self) -> float:
        """Calculate communication efficiency based on pheromone usage"""
        if not self.swarm_state.pheromone_map:
            return 0.0
        
        active_trails = sum(1 for path_data in self.swarm_state.pheromone_map.values() 
                          if path_data.get("strength", 0) > 0.1)
        total_trails = len(self.swarm_state.pheromone_map)
        
        return active_trails / total_trails if total_trails > 0 else 0.0
    
    def _get_top_solutions(self, count: int) -> List[Dict[str, Any]]:
        """Get top N solutions from swarm"""
        solutions = []
        for agent_id, swarm_agent in self.swarm_agents.items():
            if swarm_agent.local_best:
                solutions.append({
                    "agent_id": agent_id,
                    "fitness": swarm_agent.local_best["fitness"],
                    "solution": swarm_agent.local_best.get("result", {})
                })
        
        solutions.sort(key=lambda x: x["fitness"], reverse=True)
        return solutions[:count]
    
    def _get_current_swarm_state(self) -> Dict[str, Any]:
        """Get current swarm state for error reporting"""
        return {
            "agent_count": len(self.swarm_agents),
            "generation": self.swarm_state.generation,
            "global_fitness": self.swarm_state.global_fitness,
            "diversity_index": self.swarm_state.diversity_index
        }
    
    async def _handle_fitness_update(self, event_data: Dict[str, Any]):
        """Handle fitness update events"""
        logger.debug(f"Fitness update: {event_data}")
    
    async def _handle_pheromone_deposit(self, event_data: Dict[str, Any]):
        """Handle pheromone deposit events"""
        agent_id = event_data.get("agent_id")
        strength = event_data.get("strength", 0.1)
        
        if agent_id in self.swarm_agents:
            swarm_agent = self.swarm_agents[agent_id]
            for neighbor_id in swarm_agent.neighbors:
                path_key = f"{agent_id}->{neighbor_id}"
                if path_key in self.swarm_state.pheromone_map:
                    self.swarm_state.pheromone_map[path_key]["strength"] += strength
    
    async def _handle_convergence(self, event_data: Dict[str, Any]):
        """Handle swarm convergence events"""
        logger.info(f"Swarm convergence detected: {event_data}")
    
    async def _deposit_pheromones(self, agent_id: str, result: Dict[str, Any]):
        """Deposit pheromones based on agent result quality"""
        fitness = self._calculate_fitness(result)
        await self.event_bus.publish("pheromone_deposit", {
            "agent_id": agent_id,
            "strength": fitness * 0.1,
            "result_quality": fitness
        })