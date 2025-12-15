"""
Workflow DNA Evolution Service
워크플로우 DNA 진화 서비스 - 2025 Future Roadmap 구현
"""

import asyncio
import json
import uuid
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from collections import defaultdict, deque
import random
import copy

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class GeneType(Enum):
    """유전자 유형"""
    PERFORMANCE = "performance"      # 성능 유전자
    RELIABILITY = "reliability"      # 신뢰성 유전자
    EFFICIENCY = "efficiency"        # 효율성 유전자
    ADAPTABILITY = "adaptability"    # 적응성 유전자
    CREATIVITY = "creativity"        # 창의성 유전자

class ExperimentStatus(Enum):
    """실험 상태"""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXTINCT = "extinct"

@dataclass
class WorkflowGene:
    """워크플로우 유전자"""
    id: str
    name: str
    type: GeneType
    value: float  # 0.0 - 1.0
    dominance: float  # 0.0 - 1.0
    mutation_rate: float
    expression_level: float  # 0.0 - 1.0
    interactions: List[str]  # 상호작용하는 다른 유전자 ID들

@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    speed: float = 0.0
    accuracy: float = 0.0
    efficiency: float = 0.0
    adaptability: float = 0.0
    innovation: float = 0.0

@dataclass
class MutationEvent:
    """돌연변이 이벤트"""
    generation: int
    gene_id: str
    old_value: float
    new_value: float
    impact: float

@dataclass
class WorkflowDNA:
    """워크플로우 DNA"""
    id: str
    name: str
    generation: int
    genes: List[WorkflowGene]
    fitness_score: float
    performance_metrics: PerformanceMetrics
    parent_ids: List[str]
    mutation_history: List[MutationEvent]
    survival_probability: float
    age: int
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class GenerationStats:
    """세대 통계"""
    generation: int
    best_fitness: float
    average_fitness: float
    diversity_index: float
    extinction_events: int
    population_size: int
    mutation_count: int
    crossover_count: int

@dataclass
class EvolutionExperiment:
    """진화 실험"""
    id: str
    name: str
    population_size: int
    current_generation: int
    max_generations: int
    mutation_rate: float
    crossover_rate: float
    selection_pressure: float
    fitness_function: str
    population: List[WorkflowDNA]
    evolution_history: List[GenerationStats]
    status: ExperimentStatus
    created_at: datetime = field(default_factory=datetime.now)

class WorkflowDNAService:
    """워크플로우 DNA 진화 서비스"""
    
    def __init__(self):
        # 데이터 저장소
        self.experiments: Dict[str, EvolutionExperiment] = {}
        self.active_experiment: Optional[str] = None
        self.evolution_logs: List[Dict[str, Any]] = []
        
        # 진화 설정
        self.config = {
            "default_population_size": 20,
            "default_max_generations": 100,
            "default_mutation_rate": 0.1,
            "default_crossover_rate": 0.7,
            "default_selection_pressure": 0.8,
            "evolution_speed": 1.0,  # 진화 속도 배수
            "diversity_threshold": 0.01,  # 다양성 임계값
            "extinction_threshold": 0.005,  # 멸종 임계값
            "elite_preservation_rate": 0.1,  # 엘리트 보존 비율
        }
        
        # 유전자 템플릿
        self.gene_templates = {
            "speed_gene": {
                "name": "Execution Speed",
                "type": GeneType.PERFORMANCE,
                "mutation_rate": 0.1,
                "interactions": ["efficiency_gene"]
            },
            "accuracy_gene": {
                "name": "Result Accuracy",
                "type": GeneType.RELIABILITY,
                "mutation_rate": 0.08,
                "interactions": ["quality_gene"]
            },
            "efficiency_gene": {
                "name": "Resource Efficiency",
                "type": GeneType.EFFICIENCY,
                "mutation_rate": 0.12,
                "interactions": ["speed_gene", "cost_gene"]
            },
            "adaptability_gene": {
                "name": "Environmental Adaptation",
                "type": GeneType.ADAPTABILITY,
                "mutation_rate": 0.15,
                "interactions": ["learning_gene"]
            },
            "creativity_gene": {
                "name": "Solution Innovation",
                "type": GeneType.CREATIVITY,
                "mutation_rate": 0.2,
                "interactions": ["adaptability_gene"]
            }
        }
        
        # 초기 실험 생성
        self._create_initial_experiment()
        
        logger.info("Workflow DNA Service initialized")
    
    def _create_initial_experiment(self):
        """초기 실험 생성"""
        try:
            experiment_id = "exp_alpha"
            
            # 초기 개체군 생성
            initial_population = self._generate_initial_population(20)
            
            experiment = EvolutionExperiment(
                id=experiment_id,
                name="Workflow Evolution Experiment Alpha",
                population_size=20,
                current_generation=0,
                max_generations=100,
                mutation_rate=0.1,
                crossover_rate=0.7,
                selection_pressure=0.8,
                fitness_function="multi_objective",
                population=initial_population,
                evolution_history=[self._calculate_generation_stats(initial_population, 0)],
                status=ExperimentStatus.PAUSED
            )
            
            self.experiments[experiment_id] = experiment
            self.active_experiment = experiment_id
            
            logger.info(f"Initial experiment created: {experiment_id}")
            
        except Exception as e:
            logger.error(f"Failed to create initial experiment: {str(e)}", exc_info=True)
    
    def _generate_initial_population(self, size: int) -> List[WorkflowDNA]:
        """초기 개체군 생성"""
        population = []
        
        for i in range(size):
            # 유전자 생성
            genes = []
            for gene_id, template in self.gene_templates.items():
                gene = WorkflowGene(
                    id=gene_id,
                    name=template["name"],
                    type=template["type"],
                    value=random.random(),
                    dominance=random.random(),
                    mutation_rate=template["mutation_rate"],
                    expression_level=random.random(),
                    interactions=template["interactions"]
                )
                genes.append(gene)
            
            # 성능 메트릭 계산
            performance_metrics = self._calculate_performance_metrics(genes)
            
            # 적합도 점수 계산
            fitness_score = self._calculate_fitness(genes)
            
            # 워크플로우 DNA 생성
            workflow_dna = WorkflowDNA(
                id=f"workflow_{i+1}",
                name=f"Workflow Organism {i+1}",
                generation=0,
                genes=genes,
                fitness_score=fitness_score,
                performance_metrics=performance_metrics,
                parent_ids=[],
                mutation_history=[],
                survival_probability=random.random(),
                age=0
            )
            
            population.append(workflow_dna)
        
        return population
    
    def _calculate_performance_metrics(self, genes: List[WorkflowGene]) -> PerformanceMetrics:
        """성능 메트릭 계산"""
        metrics = PerformanceMetrics()
        
        for gene in genes:
            if gene.id == "speed_gene":
                metrics.speed = gene.value * gene.expression_level
            elif gene.id == "accuracy_gene":
                metrics.accuracy = gene.value * gene.expression_level
            elif gene.id == "efficiency_gene":
                metrics.efficiency = gene.value * gene.expression_level
            elif gene.id == "adaptability_gene":
                metrics.adaptability = gene.value * gene.expression_level
            elif gene.id == "creativity_gene":
                metrics.innovation = gene.value * gene.expression_level
        
        return metrics
    
    def _calculate_fitness(self, genes: List[WorkflowGene]) -> float:
        """적합도 점수 계산"""
        # 다목적 적합도 함수
        weights = {
            GeneType.PERFORMANCE: 0.3,
            GeneType.RELIABILITY: 0.25,
            GeneType.EFFICIENCY: 0.2,
            GeneType.ADAPTABILITY: 0.15,
            GeneType.CREATIVITY: 0.1
        }
        
        fitness = 0.0
        for gene in genes:
            weight = weights.get(gene.type, 0.1)
            fitness += gene.value * gene.expression_level * weight
        
        # 유전자 상호작용 보너스
        interaction_bonus = self._calculate_interaction_bonus(genes)
        fitness += interaction_bonus * 0.1
        
        return min(1.0, fitness)
    
    def _calculate_interaction_bonus(self, genes: List[WorkflowGene]) -> float:
        """유전자 상호작용 보너스 계산"""
        bonus = 0.0
        gene_dict = {gene.id: gene for gene in genes}
        
        for gene in genes:
            for interaction_id in gene.interactions:
                if interaction_id in gene_dict:
                    interacting_gene = gene_dict[interaction_id]
                    # 상호작용하는 유전자들의 값이 비슷할 때 보너스
                    similarity = 1.0 - abs(gene.value - interacting_gene.value)
                    bonus += similarity * gene.dominance * interacting_gene.dominance
        
        return bonus / len(genes) if genes else 0.0
    
    def _calculate_generation_stats(self, population: List[WorkflowDNA], generation: int) -> GenerationStats:
        """세대 통계 계산"""
        fitness_scores = [dna.fitness_score for dna in population]
        
        best_fitness = max(fitness_scores) if fitness_scores else 0.0
        average_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0.0
        diversity_index = self._calculate_diversity_index(population)
        
        return GenerationStats(
            generation=generation,
            best_fitness=best_fitness,
            average_fitness=average_fitness,
            diversity_index=diversity_index,
            extinction_events=1 if diversity_index < self.config["extinction_threshold"] else 0,
            population_size=len(population),
            mutation_count=0,  # 실제 진화 과정에서 계산
            crossover_count=0  # 실제 진화 과정에서 계산
        )
    
    def _calculate_diversity_index(self, population: List[WorkflowDNA]) -> float:
        """다양성 지수 계산 (Shannon diversity index 기반)"""
        if not population:
            return 0.0
        
        # 각 유전자별 값의 분산 계산
        gene_variances = []
        
        for i in range(len(population[0].genes)):
            values = [dna.genes[i].value for dna in population]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            gene_variances.append(variance)
        
        return sum(gene_variances) / len(gene_variances) if gene_variances else 0.0
    
    async def start_evolution(self, experiment_id: str) -> bool:
        """진화 시작"""
        try:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            experiment.status = ExperimentStatus.RUNNING
            self.active_experiment = experiment_id
            
            # 백그라운드에서 진화 실행
            asyncio.create_task(self._run_evolution_loop(experiment_id))
            
            logger.info(f"Evolution started for experiment: {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start evolution: {str(e)}", exc_info=True)
            return False
    
    async def stop_evolution(self, experiment_id: str) -> bool:
        """진화 중단"""
        try:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            experiment.status = ExperimentStatus.PAUSED
            
            logger.info(f"Evolution stopped for experiment: {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop evolution: {str(e)}", exc_info=True)
            return False
    
    async def _run_evolution_loop(self, experiment_id: str):
        """진화 루프 실행"""
        while True:
            try:
                experiment = self.experiments.get(experiment_id)
                if not experiment or experiment.status != ExperimentStatus.RUNNING:
                    break
                
                if experiment.current_generation >= experiment.max_generations:
                    experiment.status = ExperimentStatus.COMPLETED
                    break
                
                # 한 세대 진화 수행
                new_population, stats = await self._evolve_generation(experiment)
                
                # 실험 업데이트
                experiment.population = new_population
                experiment.current_generation += 1
                experiment.evolution_history.append(stats)
                
                # 멸종 확인
                if stats.diversity_index < self.config["extinction_threshold"]:
                    experiment.status = ExperimentStatus.EXTINCT
                    logger.warning(f"Experiment {experiment_id} went extinct at generation {experiment.current_generation}")
                    break
                
                # 진화 속도에 따른 대기
                await asyncio.sleep(1.0 / self.config["evolution_speed"])
                
            except Exception as e:
                logger.error(f"Evolution loop error: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _evolve_generation(self, experiment: EvolutionExperiment) -> Tuple[List[WorkflowDNA], GenerationStats]:
        """한 세대 진화"""
        try:
            # 선택
            selected = self._tournament_selection(experiment.population, experiment.population_size)
            
            # 교배 및 돌연변이
            new_population = []
            mutation_count = 0
            crossover_count = 0
            
            # 엘리트 보존
            elite_count = int(experiment.population_size * self.config["elite_preservation_rate"])
            elite = sorted(experiment.population, key=lambda x: x.fitness_score, reverse=True)[:elite_count]
            new_population.extend([self._clone_dna(dna) for dna in elite])
            
            # 나머지 개체 생성
            while len(new_population) < experiment.population_size:
                parent1 = random.choice(selected)
                parent2 = random.choice(selected)
                
                if random.random() < experiment.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2, experiment.current_generation + 1)
                    crossover_count += 1
                else:
                    child1 = self._clone_dna(parent1)
                    child2 = self._clone_dna(parent2)
                
                # 돌연변이
                if self._mutate(child1, experiment.mutation_rate):
                    mutation_count += 1
                if len(new_population) + 1 < experiment.population_size and self._mutate(child2, experiment.mutation_rate):
                    mutation_count += 1
                
                new_population.append(child1)
                if len(new_population) < experiment.population_size:
                    new_population.append(child2)
            
            # 세대 통계 계산
            stats = self._calculate_generation_stats(new_population, experiment.current_generation + 1)
            stats.mutation_count = mutation_count
            stats.crossover_count = crossover_count
            
            return new_population, stats
            
        except Exception as e:
            logger.error(f"Generation evolution failed: {str(e)}", exc_info=True)
            return experiment.population, self._calculate_generation_stats(experiment.population, experiment.current_generation)
    
    def _tournament_selection(self, population: List[WorkflowDNA], size: int) -> List[WorkflowDNA]:
        """토너먼트 선택"""
        selected = []
        tournament_size = 3
        
        for _ in range(size):
            tournament = random.sample(population, min(tournament_size, len(population)))
            winner = max(tournament, key=lambda x: x.fitness_score)
            selected.append(winner)
        
        return selected
    
    def _crossover(self, parent1: WorkflowDNA, parent2: WorkflowDNA, generation: int) -> Tuple[WorkflowDNA, WorkflowDNA]:
        """교배"""
        try:
            # 유전자 교배
            child1_genes = []
            child2_genes = []
            
            for i in range(len(parent1.genes)):
                gene1 = parent1.genes[i]
                gene2 = parent2.genes[i]
                
                # 단일점 교배
                if random.random() < 0.5:
                    child1_gene = copy.deepcopy(gene1)
                    child2_gene = copy.deepcopy(gene2)
                else:
                    child1_gene = copy.deepcopy(gene2)
                    child2_gene = copy.deepcopy(gene1)
                
                # 발현 수준 평균화
                child1_gene.expression_level = (gene1.expression_level + gene2.expression_level) / 2
                child2_gene.expression_level = (gene1.expression_level + gene2.expression_level) / 2
                
                child1_genes.append(child1_gene)
                child2_genes.append(child2_gene)
            
            # 자식 DNA 생성
            child1 = WorkflowDNA(
                id=f"workflow_{uuid.uuid4().hex[:8]}",
                name=f"Hybrid {parent1.name.split()[-1]} × {parent2.name.split()[-1]}",
                generation=generation,
                genes=child1_genes,
                fitness_score=self._calculate_fitness(child1_genes),
                performance_metrics=self._calculate_performance_metrics(child1_genes),
                parent_ids=[parent1.id, parent2.id],
                mutation_history=[],
                survival_probability=random.random(),
                age=0
            )
            
            child2 = WorkflowDNA(
                id=f"workflow_{uuid.uuid4().hex[:8]}",
                name=f"Hybrid {parent2.name.split()[-1]} × {parent1.name.split()[-1]}",
                generation=generation,
                genes=child2_genes,
                fitness_score=self._calculate_fitness(child2_genes),
                performance_metrics=self._calculate_performance_metrics(child2_genes),
                parent_ids=[parent1.id, parent2.id],
                mutation_history=[],
                survival_probability=random.random(),
                age=0
            )
            
            return child1, child2
            
        except Exception as e:
            logger.error(f"Crossover failed: {str(e)}")
            return self._clone_dna(parent1), self._clone_dna(parent2)
    
    def _mutate(self, dna: WorkflowDNA, mutation_rate: float) -> bool:
        """돌연변이"""
        mutated = False
        
        try:
            for gene in dna.genes:
                if random.random() < mutation_rate:
                    old_value = gene.value
                    
                    # 가우시안 돌연변이
                    mutation_strength = 0.1
                    new_value = gene.value + random.gauss(0, mutation_strength)
                    new_value = max(0.0, min(1.0, new_value))
                    
                    gene.value = new_value
                    
                    # 돌연변이 기록
                    mutation_event = MutationEvent(
                        generation=dna.generation,
                        gene_id=gene.id,
                        old_value=old_value,
                        new_value=new_value,
                        impact=abs(new_value - old_value)
                    )
                    
                    dna.mutation_history.append(mutation_event)
                    mutated = True
            
            if mutated:
                # 적합도 재계산
                dna.fitness_score = self._calculate_fitness(dna.genes)
                dna.performance_metrics = self._calculate_performance_metrics(dna.genes)
            
        except Exception as e:
            logger.error(f"Mutation failed: {str(e)}")
        
        return mutated
    
    def _clone_dna(self, dna: WorkflowDNA) -> WorkflowDNA:
        """DNA 복제"""
        return copy.deepcopy(dna)
    
    # Public API Methods
    
    async def get_experiments(self) -> List[Dict[str, Any]]:
        """모든 실험 조회"""
        return [self._experiment_to_dict(exp) for exp in self.experiments.values()]
    
    async def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """특정 실험 조회"""
        experiment = self.experiments.get(experiment_id)
        return self._experiment_to_dict(experiment) if experiment else None
    
    async def get_population(self, experiment_id: str) -> List[Dict[str, Any]]:
        """개체군 조회"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return []
        
        return [self._dna_to_dict(dna) for dna in experiment.population]
    
    async def get_dna_details(self, experiment_id: str, dna_id: str) -> Optional[Dict[str, Any]]:
        """특정 DNA 상세 조회"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        
        for dna in experiment.population:
            if dna.id == dna_id:
                return self._dna_to_dict(dna)
        
        return None
    
    async def perform_crossover(self, experiment_id: str, parent1_id: str, parent2_id: str) -> Dict[str, Any]:
        """교배 수행"""
        try:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return {"error": "Experiment not found"}
            
            parent1 = None
            parent2 = None
            
            for dna in experiment.population:
                if dna.id == parent1_id:
                    parent1 = dna
                elif dna.id == parent2_id:
                    parent2 = dna
            
            if not parent1 or not parent2:
                return {"error": "Parents not found"}
            
            child1, child2 = self._crossover(parent1, parent2, experiment.current_generation + 1)
            
            # 개체군에 추가
            experiment.population.extend([child1, child2])
            
            return {
                "success": True,
                "children": [self._dna_to_dict(child1), self._dna_to_dict(child2)]
            }
            
        except Exception as e:
            logger.error(f"Crossover failed: {str(e)}")
            return {"error": str(e)}
    
    async def create_experiment(self, experiment_data: Dict[str, Any]) -> str:
        """새 실험 생성"""
        try:
            experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
            
            population_size = experiment_data.get("population_size", self.config["default_population_size"])
            initial_population = self._generate_initial_population(population_size)
            
            experiment = EvolutionExperiment(
                id=experiment_id,
                name=experiment_data.get("name", f"Experiment {experiment_id}"),
                population_size=population_size,
                current_generation=0,
                max_generations=experiment_data.get("max_generations", self.config["default_max_generations"]),
                mutation_rate=experiment_data.get("mutation_rate", self.config["default_mutation_rate"]),
                crossover_rate=experiment_data.get("crossover_rate", self.config["default_crossover_rate"]),
                selection_pressure=experiment_data.get("selection_pressure", self.config["default_selection_pressure"]),
                fitness_function=experiment_data.get("fitness_function", "multi_objective"),
                population=initial_population,
                evolution_history=[self._calculate_generation_stats(initial_population, 0)],
                status=ExperimentStatus.PAUSED
            )
            
            self.experiments[experiment_id] = experiment
            
            logger.info(f"New experiment created: {experiment_id}")
            return experiment_id
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {str(e)}", exc_info=True)
            raise
    
    async def get_analytics(self, experiment_id: str) -> Dict[str, Any]:
        """분석 데이터 조회"""
        try:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return {}
            
            # 엘리트 개체 수
            elite_count = len([dna for dna in experiment.population if dna.fitness_score >= 0.8])
            
            # 평균 적합도
            avg_fitness = sum(dna.fitness_score for dna in experiment.population) / len(experiment.population)
            
            # 다양성 지수
            diversity_index = self._calculate_diversity_index(experiment.population)
            
            # 진화 트렌드
            evolution_trends = {
                "best_fitness": [stats.best_fitness for stats in experiment.evolution_history],
                "average_fitness": [stats.average_fitness for stats in experiment.evolution_history],
                "diversity_index": [stats.diversity_index for stats in experiment.evolution_history]
            }
            
            # 유전자 분포
            gene_distribution = {}
            for gene_id in self.gene_templates.keys():
                values = [dna.genes[i].value for dna in experiment.population for i, gene in enumerate(dna.genes) if gene.id == gene_id]
                if values:
                    gene_distribution[gene_id] = {
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "std": np.std(values) if len(values) > 1 else 0.0
                    }
            
            return {
                "elite_organisms": elite_count,
                "genetic_diversity": diversity_index * 100,
                "average_fitness": avg_fitness * 100,
                "evolution_trends": evolution_trends,
                "gene_distribution": gene_distribution,
                "generation_stats": experiment.evolution_history[-1].__dict__ if experiment.evolution_history else {},
                "convergence_analysis": {
                    "is_converging": diversity_index < self.config["diversity_threshold"],
                    "extinction_risk": diversity_index < self.config["extinction_threshold"] * 2,
                    "optimal_traits": self._identify_optimal_traits(experiment.population)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {str(e)}", exc_info=True)
            return {}
    
    def _identify_optimal_traits(self, population: List[WorkflowDNA]) -> List[str]:
        """최적 특성 식별"""
        optimal_traits = []
        
        try:
            # 상위 20% 개체들의 특성 분석
            top_performers = sorted(population, key=lambda x: x.fitness_score, reverse=True)[:int(len(population) * 0.2)]
            
            # 각 유전자별 평균값 계산
            gene_averages = {}
            for gene_id in self.gene_templates.keys():
                values = []
                for dna in top_performers:
                    for gene in dna.genes:
                        if gene.id == gene_id:
                            values.append(gene.value)
                
                if values:
                    avg_value = sum(values) / len(values)
                    if avg_value > 0.7:  # 높은 값을 가진 유전자
                        optimal_traits.append(f"High {self.gene_templates[gene_id]['name']}")
            
        except Exception as e:
            logger.error(f"Optimal traits identification failed: {str(e)}")
        
        return optimal_traits
    
    def _experiment_to_dict(self, experiment: EvolutionExperiment) -> Dict[str, Any]:
        """실험을 딕셔너리로 변환"""
        return {
            "id": experiment.id,
            "name": experiment.name,
            "population_size": experiment.population_size,
            "current_generation": experiment.current_generation,
            "max_generations": experiment.max_generations,
            "mutation_rate": experiment.mutation_rate,
            "crossover_rate": experiment.crossover_rate,
            "selection_pressure": experiment.selection_pressure,
            "fitness_function": experiment.fitness_function,
            "status": experiment.status.value,
            "evolution_history": [stats.__dict__ for stats in experiment.evolution_history],
            "created_at": experiment.created_at.isoformat()
        }
    
    def _dna_to_dict(self, dna: WorkflowDNA) -> Dict[str, Any]:
        """DNA를 딕셔너리로 변환"""
        return {
            "id": dna.id,
            "name": dna.name,
            "generation": dna.generation,
            "genes": [
                {
                    "id": gene.id,
                    "name": gene.name,
                    "type": gene.type.value,
                    "value": gene.value,
                    "dominance": gene.dominance,
                    "mutation_rate": gene.mutation_rate,
                    "expression_level": gene.expression_level,
                    "interactions": gene.interactions
                }
                for gene in dna.genes
            ],
            "fitness_score": dna.fitness_score,
            "performance_metrics": {
                "speed": dna.performance_metrics.speed,
                "accuracy": dna.performance_metrics.accuracy,
                "efficiency": dna.performance_metrics.efficiency,
                "adaptability": dna.performance_metrics.adaptability,
                "innovation": dna.performance_metrics.innovation
            },
            "parent_ids": dna.parent_ids,
            "mutation_history": [
                {
                    "generation": mut.generation,
                    "gene_id": mut.gene_id,
                    "old_value": mut.old_value,
                    "new_value": mut.new_value,
                    "impact": mut.impact
                }
                for mut in dna.mutation_history
            ],
            "survival_probability": dna.survival_probability,
            "age": dna.age,
            "created_at": dna.created_at.isoformat()
        }

# 싱글톤 인스턴스
_workflow_dna_service = None

def get_workflow_dna_service() -> WorkflowDNAService:
    """Workflow DNA Service 싱글톤 인스턴스 반환"""
    global _workflow_dna_service
    if _workflow_dna_service is None:
        _workflow_dna_service = WorkflowDNAService()
    return _workflow_dna_service