"""
Gemini MultiModal Workflow Templates
즉시 사용 가능한 멀티모달 워크플로우 템플릿들
"""

from typing import Dict, List, Any
from datetime import datetime

class GeminiWorkflowTemplates:
    """Gemini 3.0 기반 워크플로우 템플릿 생성기"""
    
    @staticmethod
    def get_receipt_processing_template() -> Dict[str, Any]:
        """영수증 처리 자동화 템플릿"""
        return {
            "name": "영수증 자동 처리",
            "description": "영수증 이미지를 업로드하면 자동으로 데이터를 추출하고 회계 시스템에 입력합니다",
            "category": "business_automation",
            "tags": ["gemini", "ocr", "accounting", "automation"],
            "icon": "🧾",
            "estimated_time": "30초",
            "difficulty": "beginner",
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "subtype": "manual",
                    "name": "영수증 업로드",
                    "position": {"x": 100, "y": 100},
                    "config": {
                        "title": "영수증 이미지 업로드",
                        "description": "처리할 영수증 이미지를 업로드하세요",
                        "inputs": [
                            {
                                "name": "receipt_image",
                                "type": "image",
                                "required": True,
                                "description": "영수증 이미지 파일"
                            }
                        ]
                    }
                },
                {
                    "id": "gemini_vision",
                    "type": "ai",
                    "subtype": "gemini_vision",
                    "name": "영수증 데이터 추출",
                    "position": {"x": 300, "y": 100},
                    "config": {
                        "model": "gemini-1.5-flash",
                        "temperature": 0.3,
                        "prompt": """이 영수증 이미지를 분석해서 다음 정보를 JSON 형태로 추출해주세요:
{
  "store_name": "상점명",
  "date": "날짜 (YYYY-MM-DD)",
  "time": "시간 (HH:MM)",
  "items": [
    {"name": "상품명", "quantity": 수량, "price": 가격}
  ],
  "subtotal": 소계,
  "tax": 세금,
  "total": 총액,
  "payment_method": "결제방법",
  "receipt_number": "영수증번호"
}""",
                        "output_format": "json"
                    }
                },
                {
                    "id": "data_validation",
                    "type": "logic",
                    "subtype": "condition",
                    "name": "데이터 검증",
                    "position": {"x": 500, "y": 100},
                    "config": {
                        "condition": "{{gemini_vision.structured_data.total}} > 0",
                        "true_path": "excel_export",
                        "false_path": "error_notification"
                    }
                },
                {
                    "id": "excel_export",
                    "type": "integration",
                    "subtype": "excel",
                    "name": "Excel 입력",
                    "position": {"x": 700, "y": 50},
                    "config": {
                        "file_path": "회계/영수증_{{date}}.xlsx",
                        "sheet_name": "영수증",
                        "data_mapping": {
                            "날짜": "{{gemini_vision.structured_data.date}}",
                            "상점명": "{{gemini_vision.structured_data.store_name}}",
                            "총액": "{{gemini_vision.structured_data.total}}",
                            "결제방법": "{{gemini_vision.structured_data.payment_method}}"
                        }
                    }
                },
                {
                    "id": "slack_notification",
                    "type": "integration",
                    "subtype": "slack",
                    "name": "완료 알림",
                    "position": {"x": 900, "y": 50},
                    "config": {
                        "channel": "#accounting",
                        "message": "✅ 영수증 처리 완료\n상점: {{gemini_vision.structured_data.store_name}}\n금액: {{gemini_vision.structured_data.total}}원"
                    }
                },
                {
                    "id": "error_notification",
                    "type": "integration",
                    "subtype": "slack",
                    "name": "오류 알림",
                    "position": {"x": 700, "y": 150},
                    "config": {
                        "channel": "#accounting",
                        "message": "❌ 영수증 처리 실패\n수동 확인이 필요합니다."
                    }
                }
            ],
            "connections": [
                {"from": "start", "to": "gemini_vision"},
                {"from": "gemini_vision", "to": "data_validation"},
                {"from": "data_validation", "to": "excel_export", "condition": "true"},
                {"from": "data_validation", "to": "error_notification", "condition": "false"},
                {"from": "excel_export", "to": "slack_notification"}
            ],
            "created_at": datetime.now().isoformat(),
            "roi_metrics": {
                "time_saved": "수작업 대비 90% 시간 절약",
                "accuracy": "95% 이상 정확도",
                "cost_per_execution": "$0.02"
            }
        }

    @staticmethod
    def get_meeting_summary_template() -> Dict[str, Any]:
        """회의록 자동화 템플릿"""
        return {
            "name": "회의록 자동 생성",
            "description": "회의 녹음을 업로드하면 자동으로 요약과 액션 아이템을 생성하고 팀에 공유합니다",
            "category": "productivity",
            "tags": ["gemini", "audio", "meeting", "collaboration"],
            "icon": "👥",
            "estimated_time": "2분",
            "difficulty": "beginner",
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "subtype": "manual",
                    "name": "회의 녹음 업로드",
                    "position": {"x": 100, "y": 100},
                    "config": {
                        "title": "회의 녹음 파일 업로드",
                        "inputs": [
                            {
                                "name": "meeting_audio",
                                "type": "audio",
                                "required": True,
                                "description": "회의 녹음 파일"
                            },
                            {
                                "name": "meeting_title",
                                "type": "text",
                                "required": True,
                                "description": "회의 제목"
                            },
                            {
                                "name": "attendees",
                                "type": "text",
                                "required": False,
                                "description": "참석자 목록 (선택사항)"
                            }
                        ]
                    }
                },
                {
                    "id": "gemini_audio",
                    "type": "ai",
                    "subtype": "gemini_audio",
                    "name": "회의 내용 분석",
                    "position": {"x": 300, "y": 100},
                    "config": {
                        "model": "gemini-1.5-flash",
                        "context": """이 회의 녹음을 분석해서 다음 형식으로 정리해주세요:

## 회의 요약
- 주요 논의사항
- 핵심 결정사항

## 액션 아이템
- [ ] 담당자: 할 일 (마감일)

## 다음 회의
- 일정 및 안건"""
                    }
                },
                {
                    "id": "format_summary",
                    "type": "ai",
                    "subtype": "llm",
                    "name": "요약 포맷팅",
                    "position": {"x": 500, "y": 100},
                    "config": {
                        "model": "gpt-4o-mini",
                        "prompt": """다음 회의 분석 결과를 보기 좋게 마크다운으로 포맷팅해주세요:

회의 제목: {{start.meeting_title}}
참석자: {{start.attendees}}
분석 결과: {{gemini_audio.analysis}}

최종 결과는 Slack에 공유하기 적합한 형태로 작성해주세요."""
                    }
                },
                {
                    "id": "slack_share",
                    "type": "integration",
                    "subtype": "slack",
                    "name": "팀 공유",
                    "position": {"x": 700, "y": 100},
                    "config": {
                        "channel": "#meetings",
                        "message": "📝 **{{start.meeting_title}}** 회의록\n\n{{format_summary.result}}"
                    }
                },
                {
                    "id": "google_docs",
                    "type": "integration",
                    "subtype": "google_docs",
                    "name": "문서 저장",
                    "position": {"x": 700, "y": 200},
                    "config": {
                        "folder": "회의록",
                        "title": "{{start.meeting_title}} - {{date}}",
                        "content": "{{format_summary.result}}"
                    }
                }
            ],
            "connections": [
                {"from": "start", "to": "gemini_audio"},
                {"from": "gemini_audio", "to": "format_summary"},
                {"from": "format_summary", "to": "slack_share"},
                {"from": "format_summary", "to": "google_docs"}
            ],
            "roi_metrics": {
                "time_saved": "회의 후 작업 80% 자동화",
                "accuracy": "90% 이상 정확도",
                "cost_per_execution": "$0.05"
            }
        }

    @staticmethod
    def get_product_catalog_template() -> Dict[str, Any]:
        """제품 카탈로그 자동 생성 템플릿"""
        return {
            "name": "제품 카탈로그 자동 생성",
            "description": "제품 사진을 업로드하면 자동으로 설명을 생성하고 다국어 카탈로그를 만듭니다",
            "category": "ecommerce",
            "tags": ["gemini", "vision", "translation", "catalog"],
            "icon": "📦",
            "estimated_time": "1분",
            "difficulty": "intermediate",
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "subtype": "manual",
                    "name": "제품 이미지 업로드",
                    "position": {"x": 100, "y": 100},
                    "config": {
                        "inputs": [
                            {
                                "name": "product_images",
                                "type": "image",
                                "multiple": True,
                                "required": True
                            },
                            {
                                "name": "product_category",
                                "type": "select",
                                "options": ["전자제품", "의류", "가구", "화장품", "기타"]
                            }
                        ]
                    }
                },
                {
                    "id": "gemini_analysis",
                    "type": "ai",
                    "subtype": "gemini_vision",
                    "name": "제품 분석",
                    "position": {"x": 300, "y": 100},
                    "config": {
                        "model": "gemini-1.5-pro",
                        "prompt": """이 제품 이미지를 분석해서 다음 정보를 생성해주세요:

1. 제품명 (간결하고 매력적으로)
2. 상세 설명 (특징, 장점, 사용법)
3. 주요 키워드 (SEO용)
4. 타겟 고객층
5. 추천 가격대

마케팅에 활용할 수 있도록 매력적으로 작성해주세요."""
                    }
                },
                {
                    "id": "translate_korean",
                    "type": "ai",
                    "subtype": "llm",
                    "name": "한국어 번역",
                    "position": {"x": 500, "y": 50},
                    "config": {
                        "model": "gpt-4o-mini",
                        "prompt": "다음 제품 설명을 자연스러운 한국어로 번역해주세요: {{gemini_analysis.result}}"
                    }
                },
                {
                    "id": "translate_english",
                    "type": "ai",
                    "subtype": "llm",
                    "name": "영어 번역",
                    "position": {"x": 500, "y": 150},
                    "config": {
                        "model": "gpt-4o-mini",
                        "prompt": "다음 제품 설명을 자연스러운 영어로 번역해주세요: {{gemini_analysis.result}}"
                    }
                },
                {
                    "id": "generate_catalog",
                    "type": "integration",
                    "subtype": "pdf_generator",
                    "name": "카탈로그 생성",
                    "position": {"x": 700, "y": 100},
                    "config": {
                        "template": "product_catalog",
                        "data": {
                            "korean": "{{translate_korean.result}}",
                            "english": "{{translate_english.result}}",
                            "images": "{{start.product_images}}",
                            "category": "{{start.product_category}}"
                        }
                    }
                }
            ],
            "connections": [
                {"from": "start", "to": "gemini_analysis"},
                {"from": "gemini_analysis", "to": "translate_korean"},
                {"from": "gemini_analysis", "to": "translate_english"},
                {"from": "translate_korean", "to": "generate_catalog"},
                {"from": "translate_english", "to": "generate_catalog"}
            ],
            "roi_metrics": {
                "time_saved": "카탈로그 제작 시간 95% 단축",
                "languages": "다국어 자동 지원",
                "cost_per_execution": "$0.08"
            }
        }

    @staticmethod
    def get_customer_support_template() -> Dict[str, Any]:
        """고객 지원 자동화 템플릿"""
        return {
            "name": "스마트 고객 지원",
            "description": "고객의 화면 공유와 음성을 실시간으로 분석해서 문제를 해결합니다",
            "category": "customer_support",
            "tags": ["gemini", "multimodal", "support", "realtime"],
            "icon": "🎧",
            "estimated_time": "실시간",
            "difficulty": "advanced",
            "nodes": [
                {
                    "id": "webhook_trigger",
                    "type": "trigger",
                    "subtype": "webhook",
                    "name": "고객 지원 요청",
                    "position": {"x": 100, "y": 100},
                    "config": {
                        "endpoint": "/support/request",
                        "method": "POST"
                    }
                },
                {
                    "id": "analyze_screenshot",
                    "type": "ai",
                    "subtype": "gemini_vision",
                    "name": "화면 분석",
                    "position": {"x": 300, "y": 50},
                    "config": {
                        "prompt": "이 고객의 화면 스크린샷을 분석해서 발생한 문제와 가능한 해결책을 제시해주세요."
                    }
                },
                {
                    "id": "analyze_audio",
                    "type": "ai",
                    "subtype": "gemini_audio",
                    "name": "음성 분석",
                    "position": {"x": 300, "y": 150},
                    "config": {
                        "context": "고객의 음성을 분석해서 감정 상태와 문제 상황을 파악해주세요."
                    }
                },
                {
                    "id": "generate_solution",
                    "type": "ai",
                    "subtype": "llm",
                    "name": "해결책 생성",
                    "position": {"x": 500, "y": 100},
                    "config": {
                        "prompt": """다음 정보를 종합해서 고객 문제 해결책을 제시해주세요:

화면 분석: {{analyze_screenshot.result}}
음성 분석: {{analyze_audio.analysis}}

단계별 해결 방법을 친절하게 설명해주세요."""
                    }
                },
                {
                    "id": "send_response",
                    "type": "integration",
                    "subtype": "email",
                    "name": "고객 응답",
                    "position": {"x": 700, "y": 100},
                    "config": {
                        "to": "{{webhook_trigger.customer_email}}",
                        "subject": "문제 해결 방법 안내",
                        "body": "{{generate_solution.result}}"
                    }
                }
            ],
            "connections": [
                {"from": "webhook_trigger", "to": "analyze_screenshot"},
                {"from": "webhook_trigger", "to": "analyze_audio"},
                {"from": "analyze_screenshot", "to": "generate_solution"},
                {"from": "analyze_audio", "to": "generate_solution"},
                {"from": "generate_solution", "to": "send_response"}
            ],
            "roi_metrics": {
                "response_time": "평균 응답 시간 70% 단축",
                "satisfaction": "고객 만족도 40% 향상",
                "cost_per_ticket": "$0.15"
            }
        }

    @classmethod
    def get_all_templates(cls) -> List[Dict[str, Any]]:
        """모든 Gemini 템플릿 반환"""
        return [
            cls.get_receipt_processing_template(),
            cls.get_meeting_summary_template(),
            cls.get_product_catalog_template(),
            cls.get_customer_support_template()
        ]

    @classmethod
    def get_template_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """카테고리별 템플릿 반환"""
        all_templates = cls.get_all_templates()
        return [t for t in all_templates if t.get('category') == category]

    @classmethod
    def get_beginner_templates(cls) -> List[Dict[str, Any]]:
        """초보자용 템플릿 반환"""
        all_templates = cls.get_all_templates()
        return [t for t in all_templates if t.get('difficulty') == 'beginner']