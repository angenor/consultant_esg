from app.skills.handlers.analyze_document import analyze_document
from app.skills.handlers.assemble_pdf import assemble_pdf
from app.skills.handlers.calculate_carbon import calculate_carbon
from app.skills.handlers.calculate_credit_score import calculate_credit_score
from app.skills.handlers.calculate_esg_score import calculate_esg_score
from app.skills.handlers.generate_reduction_plan import generate_reduction_plan
from app.skills.handlers.generate_report_section import generate_report_section
from app.skills.handlers.get_company_profile import get_company_profile
from app.skills.handlers.manage_action_plan import manage_action_plan
from app.skills.handlers.get_sector_benchmark import get_sector_benchmark
from app.skills.handlers.list_referentiels import list_referentiels
from app.skills.handlers.search_green_funds import search_green_funds
from app.skills.handlers.search_knowledge_base import search_knowledge_base
from app.skills.handlers.simulate_funding import simulate_funding
from app.skills.handlers.update_company_profile import update_company_profile

__all__ = [
    "analyze_document",
    "assemble_pdf",
    "calculate_carbon",
    "calculate_credit_score",
    "calculate_esg_score",
    "generate_reduction_plan",
    "generate_report_section",
    "get_company_profile",
    "get_sector_benchmark",
    "manage_action_plan",
    "update_company_profile",
    "list_referentiels",
    "search_green_funds",
    "search_knowledge_base",
    "simulate_funding",
]
