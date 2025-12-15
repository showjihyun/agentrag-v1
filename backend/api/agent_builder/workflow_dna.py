"""
Workflow DNA Evolution API
워크플로우 DNA 진화 API - 2025 Future Roadmap 구현
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from backend.services.evolution.workflow_dna_service import (
    get_workflow_dna_service,
    WorkflowDNAService,
    GeneType,
    ExperimentStatus
)
from backend.core.structured_logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/workflow-dna",
    tags=["workflow-dna"]
)

# Request/Response Models
class ExperimentCreateRequest(BaseModel):
    """실험 생성 요청"""
    name: str = Field(description="실험 이름")
    population_size: Optional[int] = Field(default=20, description="개체군 크기")
    max_generations: Optional[int] = Field(default=100, description="최대 세대 수")
    mutation_rate: Optional[float] = Field(default=0.1, description="돌연변이율")
    crossover_rate: Optional[float] = Field(default=0.7, description="교배율")
    selection_pressure: Optional[float] = Field(default=0.8, description="선택 압력")
    fitness_function: Optional[str] = Field(default="multi_objective", description="적합도 함수")

class CrossoverRequest(BaseModel):
    """교배 요청"""
    parent1_id: str = Field(description="부모 1 ID")
    parent2_id: str = Field(description="부모 2 ID")

class ExperimentsResponse(BaseModel):
    """실험 목록 응답"""
    experiments: List[Dict[str, Any]]
    total_count: int
    active_experiments: int
    completed_experiments: int

class PopulationResponse(BaseModel):
    """개체군 응답"""
    population: List[Dict[str, Any]]
    population_size: int
    generation: int
    best_fitness: float
    average_fitness: float
    diversity_index: float

class DNADetailsResponse(BaseModel):
    """DNA 상세 응답"""
    dna: Dict[str, Any]
    genetic_analysis: Dict[str, Any]
    performance_breakdown: Dict[str, float]
    evolution_path: List[str]

class AnalyticsResponse(BaseModel):
    """분석 데이터 응답"""
    elite_organisms: int
    genetic_diversity: float
    average_fitness: float
    evolution_trends: Dict[str, List[float]]
    gene_distribution: Dict[str, Dict[str, float]]
    convergence_analysis: Dict[str, Any]

class CrossoverResponse(BaseModel):
    """교배 응답"""
    success: bool
    children: List[Dict[str, Any]]
    crossover_analysis: Dict[str, Any]
    genetic_contribution: Dict[str, float]

@router.get("/experiments", response_model=ExperimentsResponse)
async def get_experiments(
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    모든 진화 실험 조회
    
    생성된 모든 워크플로우 DNA 진화 실험의 목록을 반환합니다.
    """
    try:
        logger.info("Getting all experiments")
        
        experiments = await dna_service.get_experiments()
        
        active_experiments = len([exp for exp in experiments if exp["status"] == ExperimentStatus.RUNNING.value])
        completed_experiments = len([exp for exp in experiments if exp["status"] == ExperimentStatus.COMPLETED.value])
        
        response = ExperimentsResponse(
            experiments=experiments,
            total_count=len(experiments),
            active_experiments=active_experiments,
            completed_experiments=completed_experiments
        )
        
        logger.info(f"Retrieved {len(experiments)} experiments")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get experiments: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get experiments: {str(e)}")

@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    특정 진화 실험 조회
    
    지정된 ID의 진화 실험 상세 정보를 반환합니다.
    """
    try:
        logger.info(f"Getting experiment: {experiment_id}")
        
        experiment = await dna_service.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")
        
        return experiment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment {experiment_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get experiment: {str(e)}")

@router.get("/experiments/{experiment_id}/population", response_model=PopulationResponse)
async def get_population(
    experiment_id: str,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    실험 개체군 조회
    
    지정된 실험의 현재 개체군과 통계를 반환합니다.
    """
    try:
        logger.info(f"Getting population for experiment: {experiment_id}")
        
        experiment = await dna_service.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")
        
        population = await dna_service.get_population(experiment_id)
        
        # 통계 계산
        fitness_scores = [dna["fitness_score"] for dna in population]
        best_fitness = max(fitness_scores) if fitness_scores else 0.0
        average_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0.0
        
        # 다양성 지수 계산 (간단한 버전)
        diversity_index = 0.0
        if len(population) > 1:
            gene_variances = []
            for gene_idx in range(len(population[0]["genes"])):
                values = [dna["genes"][gene_idx]["value"] for dna in population]
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                gene_variances.append(variance)
            diversity_index = sum(gene_variances) / len(gene_variances) if gene_variances else 0.0
        
        response = PopulationResponse(
            population=population,
            population_size=len(population),
            generation=experiment["current_generation"],
            best_fitness=best_fitness,
            average_fitness=average_fitness,
            diversity_index=diversity_index
        )
        
        logger.info(f"Retrieved population of {len(population)} organisms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get population: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get population: {str(e)}")

@router.get("/experiments/{experiment_id}/dna/{dna_id}", response_model=DNADetailsResponse)
async def get_dna_details(
    experiment_id: str,
    dna_id: str,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    DNA 상세 정보 조회
    
    특정 워크플로우 DNA의 상세한 유전자 정보와 분석 결과를 반환합니다.
    """
    try:
        logger.info(f"Getting DNA details: {dna_id} in experiment {experiment_id}")
        
        dna = await dna_service.get_dna_details(experiment_id, dna_id)
        if not dna:
            raise HTTPException(status_code=404, detail=f"DNA not found: {dna_id}")
        
        # 유전자 분석
        genetic_analysis = {
            "dominant_genes": [],
            "recessive_genes": [],
            "high_expression_genes": [],
            "mutation_count": len(dna["mutation_history"]),
            "genetic_stability": 1.0 - (len(dna["mutation_history"]) / max(1, dna["generation"]))
        }
        
        for gene in dna["genes"]:
            if gene["dominance"] > 0.7:
                genetic_analysis["dominant_genes"].append(gene["name"])
            elif gene["dominance"] < 0.3:
                genetic_analysis["recessive_genes"].append(gene["name"])
            
            if gene["expression_level"] > 0.8:
                genetic_analysis["high_expression_genes"].append(gene["name"])
        
        # 성능 분석
        performance_breakdown = dna["performance_metrics"]
        
        # 진화 경로
        evolution_path = []
        if dna["parent_ids"]:
            evolution_path.extend([f"Parent: {pid}" for pid in dna["parent_ids"]])
        evolution_path.append(f"Generation {dna['generation']}")
        if dna["mutation_history"]:
            evolution_path.append(f"Mutations: {len(dna['mutation_history'])}")
        
        response = DNADetailsResponse(
            dna=dna,
            genetic_analysis=genetic_analysis,
            performance_breakdown=performance_breakdown,
            evolution_path=evolution_path
        )
        
        logger.info(f"Retrieved DNA details for {dna_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get DNA details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get DNA details: {str(e)}")

@router.post("/experiments")
async def create_experiment(
    request: ExperimentCreateRequest,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    새 진화 실험 생성
    
    새로운 워크플로우 DNA 진화 실험을 생성합니다.
    """
    try:
        logger.info(f"Creating experiment: {request.name}")
        
        experiment_data = {
            "name": request.name,
            "population_size": request.population_size,
            "max_generations": request.max_generations,
            "mutation_rate": request.mutation_rate,
            "crossover_rate": request.crossover_rate,
            "selection_pressure": request.selection_pressure,
            "fitness_function": request.fitness_function
        }
        
        experiment_id = await dna_service.create_experiment(experiment_data)
        
        return {
            "success": True,
            "experiment_id": experiment_id,
            "message": f"Experiment '{request.name}' created successfully",
            "parameters": experiment_data,
            "created_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")

@router.post("/experiments/{experiment_id}/start")
async def start_evolution(
    experiment_id: str,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    진화 시작
    
    지정된 실험의 진화 과정을 시작합니다.
    """
    try:
        logger.info(f"Starting evolution for experiment: {experiment_id}")
        
        success = await dna_service.start_evolution(experiment_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to start evolution: {experiment_id}")
        
        return {
            "success": True,
            "experiment_id": experiment_id,
            "message": "Evolution started successfully",
            "started_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start evolution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start evolution: {str(e)}")

@router.post("/experiments/{experiment_id}/stop")
async def stop_evolution(
    experiment_id: str,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    진화 중단
    
    진행 중인 진화 과정을 중단합니다.
    """
    try:
        logger.info(f"Stopping evolution for experiment: {experiment_id}")
        
        success = await dna_service.stop_evolution(experiment_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to stop evolution: {experiment_id}")
        
        return {
            "success": True,
            "experiment_id": experiment_id,
            "message": "Evolution stopped successfully",
            "stopped_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop evolution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop evolution: {str(e)}")

@router.post("/experiments/{experiment_id}/crossover", response_model=CrossoverResponse)
async def perform_crossover(
    experiment_id: str,
    request: CrossoverRequest,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    유전자 교배 수행
    
    두 부모 DNA를 교배하여 새로운 자손을 생성합니다.
    """
    try:
        logger.info(f"Performing crossover in experiment {experiment_id}: {request.parent1_id} x {request.parent2_id}")
        
        result = await dna_service.perform_crossover(experiment_id, request.parent1_id, request.parent2_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # 교배 분석
        crossover_analysis = {
            "parent1_fitness": 0.0,  # 실제로는 부모 DNA에서 가져와야 함
            "parent2_fitness": 0.0,
            "child1_fitness": result["children"][0]["fitness_score"],
            "child2_fitness": result["children"][1]["fitness_score"],
            "fitness_improvement": True,  # 간단한 계산
            "genetic_diversity_increase": True
        }
        
        # 유전적 기여도
        genetic_contribution = {
            "parent1_contribution": 0.5,  # 실제로는 더 정확한 계산 필요
            "parent2_contribution": 0.5,
            "novel_mutations": 0.0
        }
        
        response = CrossoverResponse(
            success=result["success"],
            children=result["children"],
            crossover_analysis=crossover_analysis,
            genetic_contribution=genetic_contribution
        )
        
        logger.info(f"Crossover completed successfully, generated {len(result['children'])} children")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform crossover: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to perform crossover: {str(e)}")

@router.get("/experiments/{experiment_id}/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    experiment_id: str,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    진화 분석 데이터 조회
    
    실험의 진화 과정 분석 결과와 통계를 반환합니다.
    """
    try:
        logger.info(f"Getting analytics for experiment: {experiment_id}")
        
        analytics = await dna_service.get_analytics(experiment_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail=f"Analytics not found for experiment: {experiment_id}")
        
        response = AnalyticsResponse(
            elite_organisms=analytics.get("elite_organisms", 0),
            genetic_diversity=analytics.get("genetic_diversity", 0.0),
            average_fitness=analytics.get("average_fitness", 0.0),
            evolution_trends=analytics.get("evolution_trends", {}),
            gene_distribution=analytics.get("gene_distribution", {}),
            convergence_analysis=analytics.get("convergence_analysis", {})
        )
        
        logger.info(f"Retrieved analytics for experiment {experiment_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/gene-types")
async def get_gene_types():
    """
    유전자 유형 목록 조회
    
    시스템에서 지원하는 모든 유전자 유형을 반환합니다.
    """
    try:
        gene_types = [
            {
                "type": gene_type.value,
                "name": gene_type.value.replace("_", " ").title(),
                "description": {
                    "performance": "Execution speed and throughput optimization",
                    "reliability": "Error handling and system stability",
                    "efficiency": "Resource utilization and cost optimization",
                    "adaptability": "Environmental adaptation and learning",
                    "creativity": "Innovation and novel solution generation"
                }.get(gene_type.value, "Workflow characteristic"),
                "color": {
                    "performance": "#ef4444",
                    "reliability": "#3b82f6",
                    "efficiency": "#10b981",
                    "adaptability": "#f59e0b",
                    "creativity": "#8b5cf6"
                }.get(gene_type.value, "#6b7280")
            }
            for gene_type in GeneType
        ]
        
        return {
            "gene_types": gene_types,
            "total_types": len(gene_types)
        }
        
    except Exception as e:
        logger.error(f"Failed to get gene types: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get gene types: {str(e)}")

@router.get("/experiments/{experiment_id}/best-organisms")
async def get_best_organisms(
    experiment_id: str,
    limit: int = 10,
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    최고 성과 개체 조회
    
    실험에서 가장 높은 적합도를 가진 개체들을 반환합니다.
    """
    try:
        logger.info(f"Getting best organisms for experiment {experiment_id}, limit: {limit}")
        
        population = await dna_service.get_population(experiment_id)
        if not population:
            raise HTTPException(status_code=404, detail=f"Population not found for experiment: {experiment_id}")
        
        # 적합도 기준으로 정렬
        best_organisms = sorted(population, key=lambda x: x["fitness_score"], reverse=True)[:limit]
        
        # 추가 분석
        analysis = {
            "fitness_range": {
                "highest": best_organisms[0]["fitness_score"] if best_organisms else 0.0,
                "lowest": best_organisms[-1]["fitness_score"] if best_organisms else 0.0
            },
            "generation_distribution": {},
            "common_traits": []
        }
        
        # 세대 분포
        for organism in best_organisms:
            gen = organism["generation"]
            analysis["generation_distribution"][gen] = analysis["generation_distribution"].get(gen, 0) + 1
        
        # 공통 특성 (간단한 분석)
        if best_organisms:
            gene_averages = {}
            for organism in best_organisms:
                for gene in organism["genes"]:
                    gene_id = gene["id"]
                    if gene_id not in gene_averages:
                        gene_averages[gene_id] = []
                    gene_averages[gene_id].append(gene["value"])
            
            for gene_id, values in gene_averages.items():
                avg_value = sum(values) / len(values)
                if avg_value > 0.7:  # 높은 값을 가진 유전자
                    analysis["common_traits"].append(f"High {gene_id.replace('_', ' ')}")
        
        return {
            "best_organisms": best_organisms,
            "total_count": len(best_organisms),
            "analysis": analysis,
            "experiment_id": experiment_id,
            "retrieved_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best organisms: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get best organisms: {str(e)}")

@router.get("/status")
async def get_dna_system_status(
    dna_service: WorkflowDNAService = Depends(get_workflow_dna_service)
):
    """
    DNA 진화 시스템 상태 조회
    
    워크플로우 DNA 진화 시스템의 전반적인 상태와 통계를 반환합니다.
    """
    try:
        experiments = await dna_service.get_experiments()
        
        running_experiments = [exp for exp in experiments if exp["status"] == ExperimentStatus.RUNNING.value]
        completed_experiments = [exp for exp in experiments if exp["status"] == ExperimentStatus.COMPLETED.value]
        
        # 전체 개체 수 계산
        total_organisms = 0
        for exp in experiments:
            total_organisms += exp.get("population_size", 0)
        
        return {
            "total_experiments": len(experiments),
            "running_experiments": len(running_experiments),
            "completed_experiments": len(completed_experiments),
            "paused_experiments": len([exp for exp in experiments if exp["status"] == ExperimentStatus.PAUSED.value]),
            "total_organisms": total_organisms,
            "supported_gene_types": len(GeneType),
            "evolution_algorithms": ["tournament_selection", "single_point_crossover", "gaussian_mutation"],
            "fitness_functions": ["multi_objective", "weighted_sum", "pareto_optimal"],
            "system_status": "active",
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get DNA system status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get DNA system status: {str(e)}")